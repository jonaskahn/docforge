#!/usr/bin/env node
"use strict";
/* Scale-aware flow budgets shared by the flow runtimes. Not a public CLI.
 *
 * A flat budget systematically under-covers large repos: plugilo-api is
 * `project.scale.class = "large"` (900 source files) with 1,300 entry points,
 * so a budget of 15 covered 1.1% of the surface. The two knobs scale
 * separately, read from the authoritative `project.scale.class` already
 * recorded in the manifest (user overrides land in `class`, so it is never
 * re-derived here):
 *
 *   | scale.class | --max-flows default | --main-limit default |
 *   |---|---|---|
 *   | small  | 15 | 15 |
 *   | medium | 30 | 25 |
 *   | large  | 50 | 40 |
 *   | missing / unknown / pre-init | 15 | 15 |
 *
 * `--max-flows` is the candidate surface (grows with repo breadth);
 * `--main-limit` is the deep-dive document budget (bounded by review cost;
 * overflow is deferred, not dropped). An explicit value > 0 always wins;
 * explicit 0 / negative / null counts as "not passed" and falls back to the
 * scale default (documented in help text). Mirrors python/budgets.py.
 */

const fs = require("fs");
const path = require("path");

const MAX_FLOWS_BY_SCALE = { small: 15, medium: 30, large: 50 };
const MAIN_LIMIT_BY_SCALE = { small: 15, medium: 25, large: 40 };
const FALLBACK_MAX_FLOWS = 15;
const FALLBACK_MAIN_LIMIT = 15;

/** `manifest.json → project.scale.class`, or null on a missing/malformed
 * manifest or an unknown class. */
function scaleClass(repo) {
  let manifest;
  try {
    manifest = JSON.parse(fs.readFileSync(path.join(repo, ".docforge", "manifest.json"), "utf8"));
  } catch {
    return null;
  }
  const scale = manifest && manifest.project && manifest.project.scale;
  if (!scale || typeof scale !== "object") return null;
  const klass = scale.class;
  return Object.prototype.hasOwnProperty.call(MAX_FLOWS_BY_SCALE, klass) ? String(klass) : null;
}

function budgetFor(repo, byScale, fallback, explicit) {
  if (explicit != null && explicit > 0) return explicit;
  const klass = scaleClass(repo);
  if (klass === null) return fallback;
  return Object.prototype.hasOwnProperty.call(byScale, klass) ? byScale[klass] : fallback;
}

function maxFlowsFor(repo, explicit = null) {
  return budgetFor(repo, MAX_FLOWS_BY_SCALE, FALLBACK_MAX_FLOWS, explicit);
}

function mainLimitFor(repo, explicit = null) {
  return budgetFor(repo, MAIN_LIMIT_BY_SCALE, FALLBACK_MAIN_LIMIT, explicit);
}

module.exports = {
  MAX_FLOWS_BY_SCALE,
  MAIN_LIMIT_BY_SCALE,
  FALLBACK_MAX_FLOWS,
  FALLBACK_MAIN_LIMIT,
  scaleClass,
  maxFlowsFor,
  mainLimitFor,
};
