#!/usr/bin/env node
"use strict";
/** Create and maintain a Docforge 2.0 manifest from the canonical catalog. */

const fs = require("fs");
const path = require("path");

const SKILL_ROOT = path.resolve(__dirname, "..");
const CATALOG_PATH = path.join(SKILL_ROOT, ".metadata", "catalog.json");
const STATUSES = ["planned", "in_progress", "generated", "needs_review", "complete", "skipped"];
const TRANSITIONS = {
  planned: new Set(["in_progress", "skipped"]),
  in_progress: new Set(["generated", "needs_review", "skipped"]),
  generated: new Set(["needs_review", "complete", "skipped"]),
  needs_review: new Set(["in_progress", "skipped"]),
  complete: new Set(["in_progress"]),
  skipped: new Set(["planned"]),
};

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
  if (data.version !== "2.0") throw new Error(`manifest version must be 2.0: ${target}`);
  return data;
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
    provenance: { sections: [] },
    audit: null,
  };
}
function selectedStaticDocuments(catalog, repo, tier, overlays) {
  const ranks = Object.fromEntries(catalog.tiers.map((item) => [item.id, item.order]));
  const selected = [];
  for (const definition of catalog.documents) {
    const rule = definition.selection;
    if (rule.mode !== "static") continue;
    const tierSelected = ranks[rule.min_tier] <= ranks[tier];
    const matching = overlays.filter((overlay) => rule.overlays.includes(overlay));
    const triggers = overlays.filter((overlay) => (rule.include_if_overlay || []).includes(overlay));
    if (rule.overlays.length && (!tierSelected || !matching.length)) continue;
    if (!rule.overlays.length && !tierSelected && !triggers.length) continue;
    const evidence = conditionEvidence(repo, rule.condition);
    if (rule.condition && !evidence.length) continue;
    const origins = [];
    if (!rule.overlays.length && tierSelected) origins.push({ kind: "tier", id: rule.min_tier });
    for (const overlay of matching) origins.push({ kind: "overlay", id: overlay });
    for (const overlay of triggers) origins.push({ kind: "overlay", id: overlay });
    if (rule.condition) origins.push({ kind: "condition", id: rule.condition });
    selected.push(makeDocument(definition, origins, evidence));
  }
  return selected.sort((a, b) => a.write_order - b.write_order || a.path.localeCompare(b.path) || a.id.localeCompare(b.id));
}
function parseArgs(argv) {
  if (!argv.length || argv.includes("-h") || argv.includes("--help")) return { help: true };
  const command = argv[0];
  const knownCommands = new Set(["init", "add", "set", "audit", "status"]);
  if (!knownCommands.has(command)) throw new Error(`unknown command: ${argv[0]}`);
  const repeatable = new Set(["overlay"]);
  const boolean = new Set(["force"]);
  const allowed = {
    init: new Set(["repo", "tier", "overlay", "name", "force"]),
    add: new Set(["repo", "type", "id", "path"]),
    set: new Set(["repo", "id", "status"]),
    audit: new Set(["repo", "id", "mode", "verdict", "report"]),
    status: new Set(["repo"]),
  }[command];
  const result = { command, overlay: [] };
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
  if (!["spine", "diligence", "portfolio"].includes(args.tier)) return fail(`invalid tier: ${args.tier}`, 2);
  const target = manifestPath(args.repo);
  if (fs.existsSync(target) && !args.force) return fail(`manifest already exists: ${target}; pass --force to replace it`);
  const catalog = loadCatalog();
  const overlayIds = catalog.overlays.map((item) => item.id);
  const unknown = args.overlay.filter((item) => !overlayIds.includes(item));
  if (unknown.length) return fail(`unknown overlay: ${unknown[0]}; expected one of: ${overlayIds.join(", ")}`, 2);
  const overlaySet = new Set(args.overlay);
  const overlays = overlayIds.filter((item) => overlaySet.has(item));
  const docs = selectedStaticDocuments(catalog, args.repo, args.tier, overlays);
  const manifest = {
    version: "2.0",
    generated_at: nowIso(),
    project: {
      name: args.name || path.basename(path.resolve(args.repo)),
      root: path.resolve(args.repo),
      tier: args.tier,
      overlays,
    },
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
    const ranks = Object.fromEntries(catalog.tiers.map((item) => [item.id, item.order]));
    const rule = definition.selection;
    if (ranks[rule.min_tier] > ranks[manifest.project.tier]) return fail(`dynamic type ${args.type} requires tier ${rule.min_tier}`, 2);
    if (rule.overlays.length && !rule.overlays.some((overlay) => manifest.project.overlays.includes(overlay))) {
      return fail(`dynamic type ${args.type} requires overlay: ${rule.overlays.join(", ")}`, 2);
    }
    const evidence = conditionEvidence(args.repo, rule.condition);
    if (rule.condition === "ticket_evidence" && !evidence.length) return fail(`dynamic type ${args.type} requires ticket evidence in the repository`, 2);
    if (!pathMatches(definition.path, args.path)) return fail(`path '${args.path}' does not match catalog pattern '${definition.path}'`, 2);
    if (!/^[a-z0-9][a-z0-9_-]*$/.test(args.id)) return fail(`document id must use lowercase letters, digits, hyphens, or underscores: ${args.id}`, 2);
    if (manifest.documents.some((doc) => doc.id === args.id)) return fail(`document id already exists: ${args.id}`, 2);
    if (manifest.documents.some((doc) => doc.path === args.path)) return fail(`document path already exists: ${args.path}`, 2);
    const actual = { ...definition, id: args.id, path: args.path };
    const origins = [{ kind: "dynamic", id: definition.type }];
    if (rule.condition) origins.push({ kind: "condition", id: rule.condition });
    manifest.documents.push(makeDocument(actual, origins, evidence));
    manifest.documents.sort((a, b) => a.write_order - b.write_order || a.path.localeCompare(b.path) || a.id.localeCompare(b.id));
    saveManifest(args.repo, manifest);
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
    console.log(`repo: ${project.name}  tier: ${project.tier}  overlays: ${project.overlays.join(", ") || "none"}`);
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
  console.log("usage: manage_manifest.js init --repo <path> --tier <spine|diligence|portfolio> [--overlay <id>] | add --repo <path> --type <type> --id <id> --path <path> | set --repo <path> --id <id> --status <status> | audit --repo <path> --id <id> --mode <subagent|cold-pass> --verdict <PASS|FAIL> --report <path> | status --repo <path>");
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
