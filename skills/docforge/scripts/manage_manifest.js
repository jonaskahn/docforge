#!/usr/bin/env node
"use strict";
/** Create and maintain a Docforge 2.0 manifest from the canonical catalog. */

const fs = require("fs");
const path = require("path");
const { detect: detectProfiles } = require("./detect_profiles.js");
const pf = require("./provenance_frontmatter.js");

const SKILL_ROOT = path.resolve(__dirname, "..");
const CATALOG_PATH = path.join(SKILL_ROOT, ".metadata", "catalog.json");
const FLOW_INDEX_REL = path.join(".docforge", "flow-index.json");
const STATUSES = ["planned", "in_progress", "generated", "needs_review", "complete", "skipped"];
const TRANSITIONS = {
  planned: new Set(["in_progress", "skipped"]),
  in_progress: new Set(["generated", "needs_review", "skipped"]),
  generated: new Set(["needs_review", "complete", "skipped"]),
  needs_review: new Set(["in_progress", "skipped"]),
  complete: new Set(["in_progress"]),
  skipped: new Set(["planned"]),
};
const TOOL_VERSION = pf.GENERATOR_VERSION;
const MANIFEST_VERSION = "3.1";

function nowIso() {
  return new Date().toISOString().replace(/\.\d{3}Z$/, "+00:00");
}
function dumpJson(value) {
  return JSON.stringify(value, null, 2) + "\n";
}
function fail(message, code = 1) {
  process.stderr.write(`error: ${message}\n`);
  return code;
}
function loadCatalog() {
  return JSON.parse(fs.readFileSync(CATALOG_PATH, "utf8"));
}
function manifestPath(repo) {
  return path.join(repo, ".docforge", "manifest.json");
}
function loadManifest(repo) {
  const target = manifestPath(repo);
  if (!fs.existsSync(target)) throw new Error(`manifest not found: ${target}`);
  const data = JSON.parse(fs.readFileSync(target, "utf8"));
  if (data.version !== MANIFEST_VERSION) {
    throw new Error(
      `manifest must use version ${MANIFEST_VERSION}: ${target}; run migrate_metadata.js for 3.0, or replace unsupported older manifests`,
    );
  }
  return data;
}
function loadMainFlow(repo, docId, docPath) {
  const target = path.join(repo, FLOW_INDEX_REL);
  if (!fs.existsSync(target)) {
    throw new Error(`flow index not found: ${target}; run flow_index.js harvest before adding flow documents`);
  }
  let index;
  try {
    index = JSON.parse(fs.readFileSync(target, "utf8"));
  } catch (error) {
    throw new Error(`invalid flow index: ${target}: ${error.message}`);
  }
  const slug = path.posix.basename(docPath, path.posix.extname(docPath));
  const row = (index.flows || []).find((item) => item.id === docId || item.slug === slug);
  if (!row) throw new Error(`flow is not present in ${FLOW_INDEX_REL}: ${docId}`);
  if (!["main", "documented"].includes(row.status)) {
    throw new Error(`flow ${docId} is ${row.status || "unranked"}; only main flows become documents`);
  }
  return [index, row];
}
function saveManifest(repo, manifest) {
  const docs = manifest.documents;
  manifest.metadata = {
    total_documents: docs.length,
    planned: docs.filter((d) => d.status === "planned").length,
    in_progress: docs.filter((d) => d.status === "in_progress").length,
    generated: docs.filter((d) => d.status === "generated").length,
    needs_review: docs.filter((d) => d.status === "needs_review").length,
    complete: docs.filter((d) => d.status === "complete").length,
    skipped: docs.filter((d) => d.status === "skipped").length,
    last_updated: nowIso(),
  };
  const target = manifestPath(repo);
  fs.mkdirSync(path.dirname(target), { recursive: true });
  fs.writeFileSync(target, dumpJson(manifest));
}
function exists(repo, rel) {
  return fs.existsSync(path.join(repo, ...rel.split("/")));
}
function conditionEvidence(repo, condition) {
  let candidates = [];
  if (condition === "conventions_source") {
    candidates = ["CONVENTIONS.md", "docs/CONVENTIONS.md", "docs/conventions.md", ".editorconfig", "STYLEGUIDE.md"];
  } else if (condition === "ticket_evidence") {
    candidates = [".docforge/tickets.json", "tickets.json", "backlog.json", "BACKLOG.md", "docs/backlog.md", ".github/ISSUE_TEMPLATE"];
  }
  return candidates.filter((candidate) => exists(repo, candidate));
}
function validateRelativePath(value) {
  if (!value || path.posix.isAbsolute(value) || value.split("/").includes("..") || value === ".") {
    throw new Error(`path must be a safe repository-relative path: ${value}`);
  }
}
function makeDocument(definition, origins, evidence = []) {
  return {
    id: definition.id,
    type: definition.type,
    path: definition.path,
    group: definition.group,
    selection: { origins, evidence },
    status: "planned",
    requires: [...definition.requires],
    scaffold_template: definition.scaffold_template,
    instruction_file: definition.instruction_file === undefined ? null : definition.instruction_file,
    target_depth: definition.target_depth,
    write_order: definition.write_order,
    provenance_mode: definition.provenance_mode,
    audit_profile: definition.audit_profile,
    provenance: pf.scaffoldProvenance(definition.id, definition.path, {
      target_depth: definition.target_depth,
    }),
    audit: null,
  };
}
const PROFILE_DIMENSIONS = ["shapes", "platforms", "frameworks", "concerns", "audiences"];
const ORIGIN_KINDS = {
  shapes: "shape", platforms: "platform", frameworks: "framework",
  concerns: "concern", audiences: "audience",
};
function normalizeProfiles(catalog, raw) {
  const normalized = {};
  for (const dimension of PROFILE_DIMENSIONS) {
    const definitions = catalog.profiles[dimension];
    const aliases = new Map();
    for (const definition of definitions) {
      aliases.set(definition.id, definition.id);
      for (const alias of definition.aliases || []) aliases.set(alias, definition.id);
    }
    const unknown = (raw[dimension] || []).filter((value) => !aliases.has(value));
    if (unknown.length) {
      const singular = dimension === "audiences" ? "audience" : dimension.slice(0, -1);
      throw new Error(`unknown ${singular}: ${unknown[0]}; expected one of: ${definitions.map((item) => item.id).join(", ")}`);
    }
    const requested = new Set((raw[dimension] || []).map((value) => aliases.get(value)));
    normalized[dimension] = definitions.filter((item) => requested.has(item.id)).map((item) => item.id);
  }
  return normalized;
}
function matchingOrigins(rule, profiles) {
  const origins = [];
  for (const dimension of PROFILE_DIMENSIONS) {
    const accepted = (rule.selectors || {})[dimension] || [];
    for (const value of profiles[dimension] || []) {
      if (accepted.includes(value)) origins.push({ kind: ORIGIN_KINDS[dimension], id: value });
    }
  }
  return origins;
}
function addAncestorIndexes(catalog, selected) {
  const indexTypes = new Set(["folder-index", "docs-index", "portfolio-index", "decision-index", "portfolio-decisions-index", "flow-index"]);
  const definitions = new Map(catalog.documents
    .filter((item) => item.selection.mode === "static" && indexTypes.has(item.type))
    .map((item) => [item.path, item]));
  const selectedPaths = new Set(selected.map((item) => item.path));
  let changed = true;
  while (changed) {
    changed = false;
    for (const child of [...selected]) {
      let parent = path.posix.dirname(child.path);
      while (parent !== ".") {
        const candidate = path.posix.join(parent, "README.md");
        const definition = definitions.get(candidate);
        if (definition && !selectedPaths.has(candidate)) {
          selected.push(makeDocument(definition, [{ kind: "ancestor", id: child.id }]));
          selectedPaths.add(candidate);
          changed = true;
        }
        parent = path.posix.dirname(parent);
      }
    }
  }
}
function selectedStaticDocuments(catalog, repo, tier, profiles) {
  const ranks = Object.fromEntries(catalog.tiers.map((item) => [item.id, item.order]));
  const selected = [];
  for (const definition of catalog.documents) {
    const rule = definition.selection;
    if (rule.mode !== "static") continue;
    const tierSelected = ranks[rule.min_tier] <= ranks[tier];
    if (!tierSelected) continue;
    const origins = matchingOrigins(rule, profiles);
    const hasSelectors = Object.values(rule.selectors || {}).some((values) => values.length);
    if (hasSelectors && !origins.length) continue;
    const evidence = conditionEvidence(repo, rule.condition);
    if (rule.condition && !evidence.length) continue;
    if (!hasSelectors) origins.push({ kind: "tier", id: rule.min_tier });
    if (rule.condition) origins.push({ kind: "condition", id: rule.condition });
    selected.push(makeDocument(definition, origins, evidence));
  }
  addAncestorIndexes(catalog, selected);
  return selected.sort((a, b) => a.write_order - b.write_order || a.path.localeCompare(b.path) || a.id.localeCompare(b.id));
}
function parseArgs(argv) {
  if (!argv.length || argv.includes("-h") || argv.includes("--help")) return { help: true };
  const command = argv[0];
  const knownCommands = new Set(["init", "add", "set", "audit", "status"]);
  if (!knownCommands.has(command)) throw new Error(`unknown command: ${argv[0]}`);
  const repeatable = new Set(["shape", "platform", "framework", "concern", "audience", "overlay"]);
  const boolean = new Set(["force"]);
  const allowed = {
    init: new Set(["repo", "tier", "shape", "platform", "framework", "concern", "audience", "overlay", "name", "force"]),
    add: new Set(["repo", "type", "id", "path"]),
    set: new Set(["repo", "id", "status"]),
    audit: new Set(["repo", "id", "mode", "verdict", "report"]),
    status: new Set(["repo"]),
  }[command];
  const result = { command, shape: [], platform: [], framework: [], concern: [], audience: [], overlay: [] };
  for (let i = 1; i < argv.length; i++) {
    const token = argv[i];
    if (!token.startsWith("--")) throw new Error(`unexpected argument: ${token}`);
    const key = token.slice(2).replace(/-/g, "_");
    const rawKey = token.slice(2);
    if (!allowed.has(rawKey)) throw new Error(`unknown option: ${token}`);
    if (boolean.has(rawKey)) {
      result[key] = true;
      continue;
    }
    if (i + 1 >= argv.length || argv[i + 1].startsWith("--")) throw new Error(`option requires a value: ${token}`);
    const value = argv[++i];
    if (repeatable.has(rawKey)) result[key].push(value);
    else result[key] = value;
  }
  return result;
}
function required(args, names) {
  for (const name of names) if (!args[name]) throw new Error(`missing required option: --${name.replace(/_/g, "-")}`);
}
function cmdInit(args) {
  required(args, ["repo", "tier"]);
  if (args.overlay.length) return fail("--overlay is unsupported in Docforge 2.0; use --shape, --platform, --framework, --concern, or --audience", 2);
  if (!["spine", "diligence", "portfolio"].includes(args.tier)) return fail(`invalid tier: ${args.tier}`, 2);
  const target = manifestPath(args.repo);
  if (fs.existsSync(target) && !args.force) return fail(`manifest already exists: ${target}; pass --force to replace it`);
  const catalog = loadCatalog();
  let profiles;
  try {
    profiles = normalizeProfiles(catalog, {
      shapes: args.shape, platforms: args.platform, frameworks: args.framework,
      concerns: args.concern,
      audiences: args.audience.length ? args.audience : ["engineers", "beginners"],
    });
  } catch (error) {
    return fail(error.message, 2);
  }
  const docs = selectedStaticDocuments(catalog, args.repo, args.tier, profiles);
  const manifest = {
    version: MANIFEST_VERSION,
    generated_at: nowIso(),
    project: {
      name: args.name || path.basename(path.resolve(args.repo)),
      root: path.resolve(args.repo),
      tier: args.tier,
      profiles,
    },
    discovery: detectProfiles(fs.realpathSync(args.repo)),
    documents: docs,
    metadata: {},
  };
  saveManifest(args.repo, manifest);
  console.log(`Wrote ${target} — tier ${args.tier}, ${docs.length} static documents planned.`);
  return 0;
}
function dynamicDefinition(catalog, typeName) {
  const matches = catalog.documents.filter((item) => item.selection.mode === "dynamic" && item.type === typeName);
  if (!matches.length) {
    const valid = [...new Set(catalog.documents.filter((item) => item.selection.mode === "dynamic").map((item) => item.type))].sort();
    throw new Error(`unknown dynamic type: ${typeName}; expected one of: ${valid.join(", ")}`);
  }
  return matches[0];
}
function pathMatches(pattern, actual) {
  const escaped = pattern.replace(/[.*+?^${}()|[\]\\]/g, "\\$&").replace("\\{slug\\}", "[a-z0-9][a-z0-9-]*");
  return new RegExp(`^${escaped}$`).test(actual);
}
function cmdAdd(args) {
  required(args, ["repo", "type", "id", "path"]);
  try {
    const manifest = loadManifest(args.repo);
    const catalog = loadCatalog();
    const definition = dynamicDefinition(catalog, args.type);
    validateRelativePath(args.path);
    let flowIndex = null;
    let flowRow = null;
    if (args.type === "flow") [flowIndex, flowRow] = loadMainFlow(args.repo, args.id, args.path);
    const ranks = Object.fromEntries(catalog.tiers.map((item) => [item.id, item.order]));
    const rule = definition.selection;
    if (ranks[rule.min_tier] > ranks[manifest.project.tier]) return fail(`dynamic type ${args.type} requires tier ${rule.min_tier}`, 2);
    const selectors = rule.selectors || {};
    const profileOrigins = matchingOrigins(rule, manifest.project.profiles);
    if (Object.values(selectors).some((values) => values.length) && !profileOrigins.length) {
      const requirements = Object.entries(selectors)
        .filter(([, values]) => values.length)
        .map(([dimension, values]) => `${ORIGIN_KINDS[dimension]}: ${values.join(", ")}`)
        .join(", ");
      return fail(`dynamic type ${args.type} requires profile ${requirements}`, 2);
    }
    let evidence = conditionEvidence(args.repo, rule.condition);
    if (flowRow) {
      evidence = [FLOW_INDEX_REL, ...(flowRow.evidence || []).map((item) => String(item.artifact || "")).filter(Boolean)];
    }
    if (rule.condition === "ticket_evidence" && !evidence.length) return fail(`dynamic type ${args.type} requires ticket evidence in the repository`, 2);
    if (!pathMatches(definition.path, args.path)) return fail(`path '${args.path}' does not match catalog pattern '${definition.path}'`, 2);
    if (!/^[a-z0-9][a-z0-9_-]*$/.test(args.id)) return fail(`document id must use lowercase letters, digits, hyphens, or underscores: ${args.id}`, 2);
    if (manifest.documents.some((doc) => doc.id === args.id)) return fail(`document id already exists: ${args.id}`, 2);
    if (manifest.documents.some((doc) => doc.path === args.path)) return fail(`document path already exists: ${args.path}`, 2);
    const actual = { ...definition, id: args.id, path: args.path };
    const origins = [{ kind: "dynamic", id: definition.type }, ...profileOrigins];
    if (rule.condition) origins.push({ kind: "condition", id: rule.condition });
    manifest.documents.push(makeDocument(actual, origins, evidence));
    manifest.documents.sort((a, b) => a.write_order - b.write_order || a.path.localeCompare(b.path) || a.id.localeCompare(b.id));
    saveManifest(args.repo, manifest);
    if (flowIndex && flowRow) {
      flowRow.status = "documented";
      fs.writeFileSync(path.join(args.repo, FLOW_INDEX_REL), dumpJson(flowIndex));
    }
    console.log(`Added ${args.id} (${args.path}) as dynamic type ${args.type}.`);
    return 0;
  } catch (error) {
    return fail(error.message, 2);
  }
}
function findDocument(manifest, id) {
  const doc = manifest.documents.find((item) => item.id === id);
  if (!doc) throw new Error(`document id not found: ${id}`);
  return doc;
}
function cmdSet(args) {
  required(args, ["repo", "id", "status"]);
  if (!STATUSES.includes(args.status)) return fail(`invalid status: ${args.status}`, 2);
  try {
    const manifest = loadManifest(args.repo);
    const doc = findDocument(manifest, args.id);
    const old = doc.status;
    if (old === args.status) {
      console.log(`${args.id}: ${old} -> ${args.status}`);
      return 0;
    }
    if (!TRANSITIONS[old].has(args.status)) return fail(`invalid status transition for ${args.id}: ${old} -> ${args.status}`, 2);
    if (args.status === "complete" && (!doc.audit || doc.audit.verdict !== "PASS")) {
      return fail(`${args.id} cannot be complete without a passing independent audit`, 2);
    }
    if (args.status === "planned" || args.status === "in_progress") doc.audit = null;
    doc.status = args.status;
    saveManifest(args.repo, manifest);
    console.log(`${args.id}: ${old} -> ${args.status}`);
    return 0;
  } catch (error) {
    return fail(error.message, 2);
  }
}
function cmdAudit(args) {
  required(args, ["repo", "id", "mode", "verdict", "report"]);
  if (!["subagent", "cold-pass"].includes(args.mode)) return fail(`invalid audit mode: ${args.mode}`, 2);
  if (!["PASS", "FAIL"].includes(args.verdict)) return fail(`invalid audit verdict: ${args.verdict}`, 2);
  try {
    const manifest = loadManifest(args.repo);
    const doc = findDocument(manifest, args.id);
    if (doc.status !== "generated") return fail(`${args.id} must be generated before audit`, 2);
    validateRelativePath(args.report);
    doc.audit = { mode: args.mode, verdict: args.verdict, timestamp: nowIso(), report_path: args.report };
    if (args.verdict === "FAIL") doc.status = "needs_review";
    saveManifest(args.repo, manifest);
    console.log(`Audit ${args.id}: ${args.verdict} (${args.mode}) -> ${args.report}`);
    return 0;
  } catch (error) {
    return fail(error.message, 2);
  }
}
function cmdStatus(args) {
  required(args, ["repo"]);
  try {
    const manifest = loadManifest(args.repo);
    const project = manifest.project;
    console.log(`repo: ${project.name}  tier: ${project.tier}`);
    for (const dimension of PROFILE_DIMENSIONS) {
      console.log(`  ${dimension}: ${project.profiles[dimension].join(", ") || "none"}`);
    }
    console.log();
    for (const doc of manifest.documents) {
      const verdict = doc.audit ? doc.audit.verdict : "-";
      console.log(`  ${doc.status.padEnd(12)}  ${verdict.padEnd(4)}  ${doc.id.padEnd(28)}  ${doc.path}`);
    }
    const c = manifest.metadata;
    console.log();
    console.log(`${c.total_documents} documents: planned=${c.planned} in_progress=${c.in_progress} generated=${c.generated} needs_review=${c.needs_review} complete=${c.complete} skipped=${c.skipped}`);
    return 0;
  } catch (error) {
    return fail(error.message, 2);
  }
}
function usage() {
  console.log("usage: manage_manifest.js init --repo <path> --tier <spine|diligence|portfolio> [--shape <id>] [--platform <id>] [--framework <id>] [--concern <id>] [--audience <id>] | add --repo <path> --type <type> --id <id> --path <path> | set --repo <path> --id <id> --status <status> | audit --repo <path> --id <id> --mode <subagent|cold-pass> --verdict <PASS|FAIL> --report <path> | status --repo <path>");
}
function main() {
  let args;
  try {
    args = parseArgs(process.argv.slice(2));
    if (args.help) {
      usage();
      return 0;
    }
    if (!args.repo || !fs.existsSync(args.repo) || !fs.statSync(args.repo).isDirectory()) {
      return fail(`not a directory: ${args.repo || ""}`, 2);
    }
    return { init: cmdInit, add: cmdAdd, set: cmdSet, audit: cmdAudit, status: cmdStatus }[args.command](args);
  } catch (error) {
    usage();
    return fail(error.message, 2);
  }
}
process.exit(main());
