#!/usr/bin/env node
"use strict";
/** Validate and apply discovery-gate judgments (offline; no model I/O). */

const fs = require("fs");
const path = require("path");

const SKILL_ROOT = path.resolve(fs.realpathSync(__dirname), "..", "..", "..");
const GATE_SCHEMA_PATH = path.join(SKILL_ROOT, ".metadata", "discovery-gate-schema.json");
const ACTIONS = new Set(["promote", "keep", "demote", "drop", "propose"]);
const CONFIDENCES = new Set(["confirmed", "candidate", "suppressed"]);
const DIMENSIONS = new Set(["shapes", "platforms", "frameworks", "concerns", "audiences"]);

function needsGate(detections, cues) {
  if ((detections || []).some((item) => item.confidence === "candidate")) return true;
  if ((detections || []).some((item) => (item.ambiguous_with || []).length)) return true;
  for (const cue of cues || []) {
    if ((cue.candidate_profiles || []).length >= 2) return true;
  }
  return false;
}

function catalogIdSet(pack) {
  const allowed = new Set();
  const catalogIds = pack.catalog_ids || {};
  for (const [dimension, ids] of Object.entries(catalogIds)) {
    for (const id of ids) allowed.add(`${dimension}\0${id}`);
  }
  for (const item of pack.detections || []) allowed.add(`${item.dimension}\0${item.id}`);
  for (const cue of pack.cues || []) {
    for (const row of cue.candidate_profiles || []) allowed.add(`${row.dimension}\0${row.id}`);
  }
  return allowed;
}

function validateJudgment(judgment, pack) {
  const errors = [];
  if (!judgment || typeof judgment !== "object" || Array.isArray(judgment)) {
    return ["judgment must be an object"];
  }
  if (judgment.version !== 1) errors.push("judgment.version must be 1");
  if (typeof judgment.notes_for_user !== "string") errors.push("judgment.notes_for_user must be a string");
  if (!Array.isArray(judgment.decisions)) {
    errors.push("judgment.decisions must be an array");
    return errors;
  }
  const allowed = catalogIdSet(pack);
  const seen = new Set();
  judgment.decisions.forEach((decision, index) => {
    const label = `decisions[${index}]`;
    if (!decision || typeof decision !== "object") {
      errors.push(`${label}: must be an object`);
      return;
    }
    const { dimension, id, action, confidence, reason } = decision;
    const grounded = decision.grounded_cues;
    if (!DIMENSIONS.has(dimension)) errors.push(`${label}: unknown dimension`);
    if (typeof id !== "string" || !id) errors.push(`${label}: id required`);
    if (!ACTIONS.has(action)) errors.push(`${label}: invalid action`);
    if (!CONFIDENCES.has(confidence)) errors.push(`${label}: invalid confidence`);
    if (typeof reason !== "string" || !reason.trim()) errors.push(`${label}: reason required`);
    if (grounded != null && !Array.isArray(grounded)) errors.push(`${label}: grounded_cues must be an array`);
    const key = `${dimension}\0${id}`;
    if (seen.has(key)) errors.push(`${label}: duplicate decision for ${dimension}:${id}`);
    seen.add(key);
    if (DIMENSIONS.has(dimension) && typeof id === "string" && !allowed.has(key)) {
      errors.push(`${label}: id not in pack catalog_ids or candidate_profiles`);
    }
    if (action === "propose" && !allowed.has(key)) {
      errors.push(`${label}: propose target must appear in pack candidates`);
    }
  });
  return errors;
}

function applyJudgment(detections, judgment, pack) {
  const effectivePack = pack || { catalog_ids: {}, detections, cues: [] };
  const errors = validateJudgment(judgment, effectivePack);
  if (errors.length) {
    return {
      ok: false,
      errors,
      recommended: detections.filter((item) => item.confidence === "confirmed"),
      also_possible: detections.filter((item) => item.confidence === "candidate"),
      dismissed: [],
      detections,
      notes_for_user: "",
    };
  }
  const byKey = new Map();
  for (const item of detections) byKey.set(`${item.dimension}\0${item.id}`, { ...item });
  const recommendedKeys = [];
  const alsoKeys = [];
  const dismissedKeys = [];
  const decided = new Set();

  for (const decision of judgment.decisions || []) {
    const key = `${decision.dimension}\0${decision.id}`;
    decided.add(key);
    let row = byKey.get(key);
    if (!row) {
      row = {
        dimension: decision.dimension,
        id: decision.id,
        confidence: decision.confidence || "candidate",
        evidence: [],
        match_strength: "weak",
        cues: [...(decision.grounded_cues || [])],
        ambiguous_with: [],
      };
    }
    row = { ...row };
    row.gate_action = decision.action;
    row.gate_reason = decision.reason || "";
    if (CONFIDENCES.has(decision.confidence)) {
      row.confidence = decision.confidence === "suppressed" ? "candidate" : decision.confidence;
    }
    byKey.set(key, row);
    if (decision.action === "promote" || decision.action === "propose") recommendedKeys.push(key);
    else if (decision.action === "keep") {
      if (row.confidence === "confirmed" || row.match_strength === "strong") recommendedKeys.push(key);
      else alsoKeys.push(key);
    } else if (decision.action === "demote") alsoKeys.push(key);
    else if (decision.action === "drop") dismissedKeys.push(key);
  }

  for (const [key, row] of byKey.entries()) {
    if (decided.has(key)) continue;
    if (row.confidence === "confirmed") recommendedKeys.push(key);
    else alsoKeys.push(key);
  }

  function materialize(keys) {
    const rows = [];
    const seen = new Set();
    keys.forEach((key, index) => {
      if (seen.has(key) || !byKey.has(key)) return;
      seen.add(key);
      rows.push({ ...byKey.get(key), prefer_rank: index + 1 });
    });
    return rows;
  }

  return {
    ok: true,
    errors: [],
    recommended: materialize(recommendedKeys),
    also_possible: materialize(alsoKeys),
    dismissed: materialize(dismissedKeys),
    detections: [...byKey.keys()].sort().map((key) => byKey.get(key)),
    notes_for_user: judgment.notes_for_user || "",
  };
}

function loadSchema() {
  return JSON.parse(fs.readFileSync(GATE_SCHEMA_PATH, "utf8"));
}

module.exports = { needsGate, validateJudgment, applyJudgment, loadSchema };
