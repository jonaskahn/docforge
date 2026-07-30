#!/usr/bin/env node
"use strict";
/** Query the split Docforge catalog. Agents and scripts use this — not raw files. */

const fs = require("fs");
const path = require("path");
const { dumpJson, fail } = require("./_util");

const SKILL_ROOT = path.resolve(__dirname, "..");
const CATALOG_DIR = path.join(SKILL_ROOT, ".metadata", "catalog");
const INDEX_PATH = path.join(CATALOG_DIR, "index.json");
const TYPES_DIR = path.join(CATALOG_DIR, "types");
const PROFILES_DIR = path.join(CATALOG_DIR, "profiles");
const CONTRACTS_DIR = path.join(SKILL_ROOT, "references", "catalog-contracts");
const PROFILE_DIMENSIONS = ["shapes", "platforms", "frameworks", "concerns", "audiences"];
const ALLOWED_DOMINANT_FORMS = new Set([
  null,
  undefined,
  "table",
  "flowchart",
  "sequenceDiagram",
  "erDiagram",
]);
const REQUIRED_DOC_FIELDS = [
  "id",
  "type",
  "path",
  "group",
  "selection",
  "scaffold_template",
  "requires",
  "target_depth",
  "write_order",
  "provenance_mode",
  "audit_profile",
];

function loadIndex() {
  if (!fs.existsSync(INDEX_PATH)) throw new Error(`catalog index not found: ${INDEX_PATH}`);
  return JSON.parse(fs.readFileSync(INDEX_PATH, "utf8"));
}

function loadProfile(dimension) {
  const aliases = {
    shape: "shapes",
    platform: "platforms",
    framework: "frameworks",
    concern: "concerns",
    audience: "audiences",
  };
  dimension = aliases[dimension] || dimension;
  if (!PROFILE_DIMENSIONS.includes(dimension)) {
    throw new Error(
      `unknown profile dimension: ${dimension}; expected one of: ${PROFILE_DIMENSIONS.join(", ")}`,
    );
  }
  const target = path.join(PROFILES_DIR, `${dimension}.json`);
  if (!fs.existsSync(target)) throw new Error(`profile file not found: ${target}`);
  return JSON.parse(fs.readFileSync(target, "utf8"));
}

function loadProfiles() {
  const profiles = {};
  for (const dimension of PROFILE_DIMENSIONS) profiles[dimension] = loadProfile(dimension);
  return profiles;
}

function loadType(docId) {
  const target = path.join(TYPES_DIR, `${docId}.json`);
  if (!fs.existsSync(target)) throw new Error(`unknown document type id: ${docId}`);
  return JSON.parse(fs.readFileSync(target, "utf8"));
}

function loadAllTypes() {
  return loadIndex().document_types.map((row) => loadType(row.id));
}

function asLegacyCatalog() {
  const index = loadIndex();
  const tiers = index.tiers;
  const tierList = Array.isArray(tiers)
    ? tiers
    : Object.entries(tiers).map(([id, meta]) => ({ id, order: meta.order }));
  return {
    $schema: "catalog-schema.json",
    version: index.version,
    tiers: tierList,
    profiles: loadProfiles(),
    groups: index.groups || [],
    capabilities: index.capabilities || [],
    documents: loadAllTypes(),
    cue_hints: index.cue_hints || [],
  };
}

function tierRows(tier) {
  const index = loadIndex();
  const tiers = index.tiers;
  const known = Array.isArray(tiers) ? new Set(tiers.map((t) => t.id)) : new Set(Object.keys(tiers));
  if (!known.has(tier)) throw new Error(`unknown tier: ${tier}`);
  return index.document_types.filter((row) => row.tier === tier);
}

function mergedRecord(docId) {
  const index = loadIndex();
  const row = index.document_types.find((r) => r.id === docId);
  if (!row) throw new Error(`unknown document type id: ${docId}`);
  return { ...loadType(docId), tier: row.tier, index_path: row.path };
}

function normalizeProfileIds(dimension, values, profiles) {
  const aliases = {};
  for (const definition of profiles[dimension]) {
    aliases[definition.id] = definition.id;
    for (const alias of definition.aliases || []) aliases[alias] = definition.id;
  }
  const resolved = [];
  for (const value of values) {
    if (!(value in aliases)) throw new Error(`unknown ${dimension.slice(0, -1)}: ${value}`);
    const canonical = aliases[value];
    if (!resolved.includes(canonical)) resolved.push(canonical);
  }
  return resolved;
}

function applicable(options = {}) {
  const index = loadIndex();
  const profiles = loadProfiles();
  const selected = {
    shapes: normalizeProfileIds("shapes", options.shape || [], profiles),
    platforms: normalizeProfileIds("platforms", options.platform || [], profiles),
    frameworks: normalizeProfileIds("frameworks", options.framework || [], profiles),
    concerns: normalizeProfileIds("concerns", options.concern || [], profiles),
    audiences: normalizeProfileIds("audiences", options.audience || [], profiles),
  };
  const tiers = index.tiers;
  const ranks = Array.isArray(tiers)
    ? Object.fromEntries(tiers.map((t) => [t.id, t.order]))
    : Object.fromEntries(Object.entries(tiers).map(([id, meta]) => [id, meta.order]));
  const tier = options.tier || "diligence";
  if (!(tier in ranks)) throw new Error(`unknown tier: ${tier}`);
  const tierRank = ranks[tier];
  const ids = [];
  for (const row of index.document_types) {
    const detail = loadType(row.id);
    const rule = detail.selection;
    if (rule.mode === "dynamic" && !options.includeDynamic) continue;
    if (ranks[rule.min_tier] > tierRank) continue;
    const selectors = rule.selectors || {};
    const hasSelectors = Object.values(selectors).some((v) => v && v.length);
    if (hasSelectors) {
      let matched = false;
      for (const [dimension, values] of Object.entries(selectors)) {
        if (dimension === "frameworks") continue;
        const selectedValues = selected[dimension] || [];
        if (values.some((value) => selectedValues.includes(value))) {
          matched = true;
          break;
        }
      }
      if (!matched) continue;
    }
    ids.push(detail.id);
  }
  return ids;
}

function validate() {
  const errors = [];
  let index;
  try {
    index = loadIndex();
  } catch (error) {
    return [error.message];
  }
  if (index.version !== "2.4.0") {
    errors.push(`catalog version must be 2.4.0, got ${index.version}`);
  }
  for (const key of ["tiers", "groups", "capabilities", "document_types"]) {
    if (!(key in index)) errors.push(`index.json missing ${key}`);
  }
  const tiers = index.tiers || {};
  const tierIds = Array.isArray(tiers) ? new Set(tiers.map((t) => t.id)) : new Set(Object.keys(tiers));

  const profiles = {};
  const profileIds = {};
  for (const dimension of PROFILE_DIMENSIONS) {
    const target = path.join(PROFILES_DIR, `${dimension}.json`);
    if (!fs.existsSync(target)) {
      errors.push(`missing profile file: ${path.basename(target)}`);
      profiles[dimension] = [];
      profileIds[dimension] = new Set();
      continue;
    }
    const definitions = JSON.parse(fs.readFileSync(target, "utf8"));
    profiles[dimension] = definitions;
    const ids = new Set(definitions.map((item) => item.id));
    if (ids.size !== definitions.length) errors.push(`${dimension}: duplicate profile id`);
    profileIds[dimension] = ids;
    const names = {};
    for (const item of definitions) {
      for (const name of [item.id, ...(item.aliases || [])]) {
        if (typeof name !== "string" || !/^[a-z0-9][a-z0-9-]*$/.test(name)) {
          errors.push(`${dimension}: invalid profile name ${name}`);
          continue;
        }
        if (name in names) {
          errors.push(
            `${dimension}: profile name collision ${name} between ${names[name]} and ${item.id}`,
          );
        }
        names[name] = item.id;
      }
    }
  }

  const indexIds = (index.document_types || []).map((row) => row.id);
  if (new Set(indexIds).size !== indexIds.length) {
    errors.push("index.json has duplicate document type ids");
  }
  const typeFiles = new Set(
    fs.readdirSync(TYPES_DIR).filter((name) => name.endsWith(".json")).map((name) => name.slice(0, -5)),
  );
  for (const docId of indexIds) {
    if (!typeFiles.has(docId)) errors.push(`index references missing type file: ${docId}.json`);
  }
  for (const stem of [...typeFiles].sort()) {
    if (!indexIds.includes(stem)) errors.push(`orphan type file not in index: ${stem}.json`);
  }

  const groups = new Set(index.groups || []);
  const capabilities = new Set(index.capabilities || []);
  const staticIds = new Set();
  const staticPaths = new Set();
  const dynamicTypes = new Set();
  let contractTypes = new Set();
  if (fs.existsSync(CONTRACTS_DIR)) {
    contractTypes = new Set(
      fs
        .readdirSync(CONTRACTS_DIR)
        .filter((name) => name.endsWith(".md") && name !== "README.md")
        .map((name) => name.slice(0, -3)),
    );
  }

  for (const docId of indexIds) {
    let doc;
    try {
      doc = loadType(docId);
    } catch (error) {
      errors.push(error.message);
      continue;
    }
    const missing = REQUIRED_DOC_FIELDS.filter((field) => !(field in doc));
    if (missing.length) {
      errors.push(`${docId}: missing fields: ${missing.join(", ")}`);
      continue;
    }
    if (doc.id !== docId) errors.push(`${docId}: id field mismatch (${doc.id})`);
    const selection = doc.selection || {};
    if (!groups.has(doc.group)) errors.push(`${docId}: unknown group ${doc.group}`);
    if (!tierIds.has(selection.min_tier)) {
      errors.push(`${docId}: unknown tier ${selection.min_tier}`);
    }
    const selectors = selection.selectors || {};
    if (selectors.frameworks && selectors.frameworks.length) {
      errors.push(`${docId}: frameworks may tailor evidence but must not select documents`);
    }
    for (const [dimension, values] of Object.entries(selectors)) {
      if (!(dimension in profileIds)) {
        errors.push(`${docId}: unknown selector dimension ${dimension}`);
        continue;
      }
      for (const value of values) {
        if (!profileIds[dimension].has(value)) {
          errors.push(`${docId}: unknown ${dimension} selector ${value}`);
        }
      }
    }
    for (const requirement of doc.requires || []) {
      if (!capabilities.has(requirement)) {
        errors.push(`${docId}: unknown requirement ${requirement}`);
      }
    }
    if (!Number.isInteger(doc.write_order)) {
      errors.push(`${docId}: write_order must be an integer`);
    }
    if (!ALLOWED_DOMINANT_FORMS.has(doc.dominant_form)) {
      errors.push(`${docId}: invalid dominant_form ${JSON.stringify(doc.dominant_form)}`);
    }
    if (contractTypes.size && !contractTypes.has(doc.type)) {
      errors.push(`${docId}: document type missing from catalog-contracts/`);
    }
    const template = path.join(SKILL_ROOT, "assets", "templates", doc.scaffold_template);
    if (!fs.existsSync(template)) {
      errors.push(`${docId}: missing template ${doc.scaffold_template}`);
    }
    if (doc.instruction_file) {
      const instruction = path.join(SKILL_ROOT, "instructions", doc.instruction_file);
      if (!fs.existsSync(instruction)) {
        errors.push(`${docId}: missing instruction ${doc.instruction_file}`);
      }
    }
    if (selection.mode === "static") {
      if (staticIds.has(doc.id)) errors.push(`duplicate static id: ${doc.id}`);
      if (staticPaths.has(doc.path)) errors.push(`duplicate static path: ${doc.path}`);
      staticIds.add(doc.id);
      staticPaths.add(doc.path);
    } else if (selection.mode === "dynamic") {
      if (dynamicTypes.has(doc.type)) errors.push(`duplicate dynamic type: ${doc.type}`);
      dynamicTypes.add(doc.type);
    } else {
      errors.push(`${docId}: selection.mode must be static or dynamic`);
    }
  }

  const infra = (profiles.shapes || []).find((item) => item.id === "infrastructure-platform");
  if (!infra) {
    errors.push("shapes: infrastructure-platform missing");
  } else {
    const patterns = new Set((infra.signals || []).map((s) => s.pattern));
    for (const required of ["ansible.cfg", "**/kustomization.yaml", "**/playbook*.yml"]) {
      if (!patterns.has(required)) {
        errors.push(`infrastructure-platform missing signal pattern ${required}`);
      }
    }
    const aliases = new Set(infra.aliases || []);
    for (const alias of ["deployment-config", "iac"]) {
      if (!aliases.has(alias)) {
        errors.push(`infrastructure-platform missing alias ${alias}`);
      }
    }
  }
  return errors;
}

function parseArgs(argv) {
  const args = {
    shape: [],
    platform: [],
    framework: [],
    concern: [],
    audience: [],
    applicableTier: "diligence",
    includeDynamic: false,
  };
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    const next = () => {
      i += 1;
      return argv[i];
    };
    if (arg === "--tier") args.tier = next();
    else if (arg === "--id") args.docId = next();
    else if (arg === "--ids") args.ids = next();
    else if (arg === "--profile") args.profile = next();
    else if (arg === "--applicable") args.applicable = true;
    else if (arg === "--shape") args.shape.push(next());
    else if (arg === "--platform") args.platform.push(next());
    else if (arg === "--framework") args.framework.push(next());
    else if (arg === "--concern") args.concern.push(next());
    else if (arg === "--audience") args.audience.push(next());
    else if (arg === "--applicable-tier") args.applicableTier = next();
    else if (arg === "--include-dynamic") args.includeDynamic = true;
    else if (arg === "--legacy") args.legacy = true;
    else if (arg === "--validate") args.validate = true;
    else throw new Error(`unknown flag: ${arg}`);
  }
  return args;
}

function main(argv = process.argv.slice(2)) {
  let args;
  try {
    args = parseArgs(argv);
  } catch (error) {
    return fail(error.message, 2);
  }
  const modes = [
    args.tier,
    args.docId,
    args.ids,
    args.profile,
    args.applicable,
    args.validate,
    args.legacy,
  ].filter(Boolean).length;
  if (modes !== 1) {
    return fail(
      "specify exactly one of --tier, --id, --ids, --profile, --applicable, --legacy, --validate",
      2,
    );
  }
  try {
    if (args.validate) {
      const errors = validate();
      if (errors.length) {
        for (const error of errors) process.stderr.write(`error: ${error}\n`);
        process.stderr.write(`${errors.length} validation error(s)\n`);
        return 1;
      }
      process.stdout.write("catalog ok\n");
      return 0;
    }
    if (args.legacy) {
      process.stdout.write(dumpJson(asLegacyCatalog()));
      return 0;
    }
    if (args.tier) {
      process.stdout.write(dumpJson(tierRows(args.tier)));
      return 0;
    }
    if (args.docId) {
      process.stdout.write(dumpJson(mergedRecord(args.docId)));
      return 0;
    }
    if (args.ids) {
      const ids = args.ids.split(",").map((part) => part.trim()).filter(Boolean);
      process.stdout.write(dumpJson(ids.map((docId) => mergedRecord(docId))));
      return 0;
    }
    if (args.profile) {
      process.stdout.write(dumpJson(loadProfile(args.profile)));
      return 0;
    }
    if (args.applicable) {
      process.stdout.write(
        dumpJson(
          applicable({
            shape: args.shape,
            platform: args.platform,
            framework: args.framework,
            concern: args.concern,
            audience: args.audience,
            tier: args.applicableTier,
            includeDynamic: args.includeDynamic,
          }),
        ),
      );
      return 0;
    }
  } catch (error) {
    return fail(error.message, 2);
  }
  return 2;
}

module.exports = {
  loadIndex,
  loadProfile,
  loadProfiles,
  loadType,
  loadAllTypes,
  asLegacyCatalog,
  tierRows,
  mergedRecord,
  applicable,
  validate,
  main,
};

if (require.main === module) {
  process.exitCode = main();
}
