#!/usr/bin/env node
"use strict";
/** Create and maintain a Docforge manifest from the canonical catalog. */

const fs = require("fs");
const path = require("path");
const { dumpJson, ensureDocforgeGitignore, ensureGitignoredDir, fail, finishDocforge, loadManifest } = require("../../common/js/_util.js");
const { planLines } = require("../../common/js/plan.js");
const { detect: detectProfiles } = require("../../catalog/js/detect_profiles.js");
const pf = require("../../common/js/provenance_frontmatter.js");
const queryCatalog = require("../../catalog/js/query_catalog.js");

const SKILL_ROOT = path.resolve(fs.realpathSync(__dirname), "..", "..", "..");
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
const USER_CONFIRMED_TRIGGERS = new Set([
  "new-trust-boundary", "per-interaction-review", "regulated-workload",
  "high-criticality", "new-external-integration", "new-data-classification",
]);

function nowIso() {
  return new Date().toISOString().replace(/\.\d{3}Z$/, "+00:00");
}
const MANIFEST_HINT =
  "run migrate_metadata.js for 3.0, or replace unsupported older manifests";

function loadCatalog() {
  return queryCatalog.asLegacyCatalog();
}
function manifestPath(repo) {
  return path.join(repo, ".docforge", "manifest.json");
}
function flowIsMainPriority(row) {
  if (row.priority === "main") return true;
  if (row.priority === "deferred") return false;
  return ["main", "documented"].includes(row.status);
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
  const status = row.status || "unranked";
  if (["main", "documented"].includes(status)) return [index, row];
  if (status === "placeholder" && flowIsMainPriority(row)) return [index, row];
  throw new Error(`flow ${docId} is ${status}; only main-priority flows become documents`);
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
  ensureDocforgeGitignore(path.dirname(target));
  ensureGitignoredDir(path.join(path.dirname(target), "tmp"));
  ensureGitignoredDir(path.join(path.dirname(target), "audits"));
}
function exists(repo, rel) {
  return fs.existsSync(path.join(repo, ...rel.split("/")));
}
function conditionEvidence(repo, condition) {
  if (condition === "conventions_source") {
    return ["CONVENTIONS.md", "docs/CONVENTIONS.md", "docs/conventions.md", ".editorconfig", "STYLEGUIDE.md"]
      .filter((candidate) => exists(repo, candidate));
  }
  if (condition === "ticket_evidence") {
    return [".docforge/tickets.json", "tickets.json", "backlog.json", "BACKLOG.md", "docs/backlog.md", ".github/ISSUE_TEMPLATE"]
      .filter((candidate) => exists(repo, candidate));
  }
  if (condition === "multi_flow_repo") {
    const target = path.join(repo, FLOW_INDEX_REL);
    if (!fs.existsSync(target) || !fs.statSync(target).isFile()) return [];
    let index;
    try {
      index = JSON.parse(fs.readFileSync(target, "utf8"));
    } catch {
      return [];
    }
    const mainCount = (index.flows || []).filter((row) => flowIsMainPriority(row)).length;
    return mainCount > 1 ? [FLOW_INDEX_REL] : [];
  }
  return [];
}
function validateRelativePath(value) {
  if (!value || path.posix.isAbsolute(value) || value.split("/").includes("..") || value === ".") {
    throw new Error(`path must be a safe repository-relative path: ${value}`);
  }
}
function validateSelectionEvidence(repo, values) {
  const validated = [];
  for (const value of values) {
    if (value.includes("\n")) throw new Error("selection evidence must not contain newlines");
    if (value.startsWith("path:")) {
      const rel = value.slice("path:".length); validateRelativePath(rel);
      if (!exists(repo, rel)) throw new Error(`selection evidence path does not exist: ${rel}`);
    } else if (value.startsWith("graph:")) {
      if (!/^graph:[a-z0-9][a-z0-9-]*:[A-Za-z0-9._:/-]+$/.test(value)) throw new Error(`invalid graph selection evidence: ${value}`);
    } else if (value.startsWith("user-confirmed:")) {
      const trigger = value.slice("user-confirmed:".length);
      if (!USER_CONFIRMED_TRIGGERS.has(trigger)) throw new Error(`unregistered user-confirmed trigger: ${trigger}`);
    } else throw new Error(`selection evidence must use path:, graph:, or user-confirmed:: ${value}`);
    if (!validated.includes(value)) validated.push(value);
  }
  return validated;
}
function makeDocument(definition, origins, evidence = [], catalogId = null) {
  // `definition` comes from the legacy-view catalog (bare filenames, kept
  // stable for --legacy CLI output); the manifest's scaffold_template must
  // be a skill-root-relative path so scaffold_docs.js can locate the file
  // after Phase 5 moved content artifacts out of one flat directory. For
  // dynamic types, `definition.id` is already the per-instance manifest id
  // by the time this runs, so callers pass the original catalog id
  // explicitly via `catalogId`.
  const detail = queryCatalog.loadType(catalogId || definition.id);
  const document = {
    id: definition.id,
    title: detail.title || definition.id.replace(/[-_]/g, " ").toLowerCase().replace(/\b\w/g, (c) => c.toUpperCase()),
    type: definition.type,
    path: definition.path,
    group: definition.group,
    selection: { origins, evidence },
    status: "planned",
    requires: [...definition.requires],
    scaffold_template: detail.template_file,
    instruction_file: detail.instruction_file === undefined ? null : detail.instruction_file,
    target_depth: definition.target_depth,
    write_order: definition.write_order,
    provenance_mode: definition.provenance_mode,
    audit_profile: definition.audit_profile,
    provenance: pf.scaffoldProvenance(definition.id, definition.path, {
      target_depth: definition.target_depth,
    }),
    audit: null,
  };
  if (detail.contract_revision !== undefined && detail.contract_revision !== null) {
    document.contract_revision = detail.contract_revision;
  }
  return document;
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
  const knownCommands = new Set(["init", "add", "set", "audit", "status", "reconcile", "finish"]);
  if (!knownCommands.has(command)) throw new Error(`unknown command: ${argv[0]}`);
  const repeatable = new Set(["shape", "platform", "framework", "concern", "audience", "overlay", "evidence"]);
  const boolean = new Set(["force", "keep-tmp"]);
  const allowed = {
    init: new Set(["repo", "tier", "shape", "platform", "framework", "concern", "audience", "overlay", "name", "force"]),
    add: new Set(["repo", "type", "id", "path", "title", "evidence"]),
    set: new Set(["repo", "id", "status"]),
    audit: new Set(["repo", "id", "mode", "verdict", "report"]),
    status: new Set(["repo"]),
    reconcile: new Set(["repo", "tier", "shape", "platform", "framework", "concern", "audience"]),
    finish: new Set(["repo", "keep-tmp"]),
  }[command];
  const result = { command, shape: [], platform: [], framework: [], concern: [], audience: [], overlay: [], evidence: [] };
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
    discovery_gate: null,
    documents: docs,
    metadata: {},
  };
  saveManifest(args.repo, manifest);
  console.log(`Wrote ${target} — tier ${args.tier}, ${docs.length} static documents planned.`);
  console.log("");
  for (const line of planLines(args.repo, manifest, path.join(args.repo, ".docforge", "flow-index.json"))) {
    console.log(line);
  }
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
    const manifest = loadManifest(manifestPath(args.repo), {
      unsupportedHint: MANIFEST_HINT,
    });
    const catalog = loadCatalog();
    const definition = dynamicDefinition(catalog, args.type);
    const fullDefinition = queryCatalog.loadType(definition.id);
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
    let evidence = [...conditionEvidence(args.repo, rule.condition), ...validateSelectionEvidence(args.repo, args.evidence || [])];
    if (flowRow) {
      evidence = [FLOW_INDEX_REL, ...(flowRow.evidence || []).map((item) => String(item.artifact || "")).filter(Boolean)];
    }
    if (rule.condition === "ticket_evidence" && !evidence.length) return fail(`dynamic type ${args.type} requires ticket evidence in the repository`, 2);
    if (fullDefinition.selection_evidence_required && !evidence.length) return fail(`dynamic type ${args.type} requires selection evidence`, 2);
    if (!pathMatches(definition.path, args.path)) return fail(`path '${args.path}' does not match catalog pattern '${definition.path}'`, 2);
    if (!/^[a-z0-9][a-z0-9_-]*$/.test(args.id)) return fail(`document id must use lowercase letters, digits, hyphens, or underscores: ${args.id}`, 2);
    if (manifest.documents.some((doc) => doc.id === args.id)) return fail(`document id already exists: ${args.id}`, 2);
    if (manifest.documents.some((doc) => doc.path === args.path)) return fail(`document path already exists: ${args.path}`, 2);
    const actual = { ...definition, id: args.id, path: args.path };
    if (args.title) actual.title = args.title;
    const origins = [{ kind: "dynamic", id: definition.type }, ...profileOrigins];
    if (rule.condition) origins.push({ kind: "condition", id: rule.condition });
    manifest.documents.push(makeDocument(actual, origins, evidence, definition.id));
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
function syncContractRevisions(catalog, docs) {
  // Refresh catalog-owned metadata on kept documents and demote written
  // documents whose content-contract revision drifted (so a revise run
  // re-grounds them even when source provenance is FRESH).
  const contractUpdated = [];
  for (const doc of docs) {
    let catalogId = null;
    if (doc.id === doc.type) {
      catalogId = doc.id;
    } else {
      for (const candidate of catalog.documents) {
        if (candidate.id === doc.id) {
          catalogId = candidate.id;
          break;
        }
        if (
          candidate.type === doc.type
          && (candidate.selection || {}).mode === "dynamic"
        ) {
          catalogId = candidate.id;
        }
      }
      if (catalogId === null) continue;
    }
    const detail = queryCatalog.loadType(catalogId);
    doc.title = detail.title || doc.title;
    doc.scaffold_template = detail.template_file;
    doc.instruction_file = detail.instruction_file === undefined ? null : detail.instruction_file;
    if (detail.target_depth !== undefined) doc.target_depth = detail.target_depth;
    if (detail.write_order !== undefined) doc.write_order = detail.write_order;
    if (detail.audit_profile !== undefined) doc.audit_profile = detail.audit_profile;
    doc.requires = [...(detail.requires || doc.requires || [])];
    const revision = detail.contract_revision === undefined ? null : detail.contract_revision;
    if (revision !== null && doc.contract_revision !== revision) {
      doc.contract_revision = revision;
      if (["generated", "needs_review", "complete"].includes(doc.status)) {
        doc.status = "in_progress";
        doc.audit = null;
      }
      contractUpdated.push(doc.id);
    }
  }
  return contractUpdated;
}
function cmdReconcile(args) {
  let manifest;
  try {
    manifest = loadManifest(manifestPath(args.repo), { unsupportedHint: MANIFEST_HINT });
  } catch (error) {
    return fail(error.message, 2);
  }
  const catalog = loadCatalog();
  const newTier = args.tier || manifest.project.tier;
  const raw = {};
  for (const dimension of PROFILE_DIMENSIONS) {
    const singular = dimension === "audiences" ? "audience" : dimension.slice(0, -1);
    let values = [...(args[singular] || [])];
    if (values.length === 1 && values[0] === "none") values = [];
    raw[dimension] = values.length ? values : (manifest.project.profiles[dimension] || []);
  }
  let profiles;
  try {
    profiles = normalizeProfiles(catalog, raw);
  } catch (error) {
    return fail(error.message, 2);
  }
  const selected = selectedStaticDocuments(catalog, args.repo, newTier, profiles);
  const selectedIds = new Set(selected.map((doc) => doc.id));
  const kept = [];
  const removed = [];
  const keptIds = new Set();
  for (const doc of manifest.documents) {
    const origins = ((doc.selection || {}).origins) || [];
    const isDynamic = origins.some((origin) => origin.kind === "dynamic");
    if (selectedIds.has(doc.id)) {
      kept.push(doc);
      keptIds.add(doc.id);
    } else if (isDynamic || doc.status !== "planned") {
      kept.push(doc);
      keptIds.add(doc.id);
    } else {
      removed.push(doc.id);
    }
  }
  const added = selected.filter((doc) => !keptIds.has(doc.id));
  const contractUpdated = syncContractRevisions(catalog, kept);
  const oldTier = manifest.project.tier;
  manifest.documents = [...kept, ...added];
  manifest.documents.sort((a, b) => a.write_order - b.write_order || a.path.localeCompare(b.path) || a.id.localeCompare(b.id));
  manifest.project.tier = newTier;
  manifest.project.profiles = profiles;
  saveManifest(args.repo, manifest);
  console.log(`Reconcile ${args.repo}:`);
  console.log(`  tier: ${oldTier} -> ${newTier}`);
  for (const dimension of PROFILE_DIMENSIONS) {
    console.log(`  ${dimension}: ${profiles[dimension].join(", ") || "(none)"}`);
  }
  if (added.length) console.log(`  added: ${added.map((doc) => doc.id).sort().join(", ")}`);
  if (removed.length) console.log(`  removed-planned: ${removed.sort().join(", ")}`);
  if (contractUpdated.length) console.log(`  contract-updated: ${contractUpdated.sort().join(", ")}`);
  console.log(`  kept: ${kept.length} documents`);
  console.log("");
  for (const line of planLines(args.repo, manifest, path.join(args.repo, ".docforge", "flow-index.json"), true)) {
    console.log(line);
  }
  return 0;
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
    const manifest = loadManifest(manifestPath(args.repo), {
      unsupportedHint: MANIFEST_HINT,
    });
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
  if (args.mode !== "cold-pass") return fail(`invalid audit mode: ${args.mode}`, 2);
  if (!["PASS", "FAIL"].includes(args.verdict)) return fail(`invalid audit verdict: ${args.verdict}`, 2);
  try {
    const manifest = loadManifest(manifestPath(args.repo), {
      unsupportedHint: MANIFEST_HINT,
    });
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
    const manifest = loadManifest(manifestPath(args.repo), {
      unsupportedHint: MANIFEST_HINT,
    });
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
function cmdFinish(args) {
  required(args, ["repo"]);
  const docforgeDir = path.join(args.repo, ".docforge");
  if (!fs.existsSync(docforgeDir) || !fs.statSync(docforgeDir).isDirectory()) {
    return fail(`.docforge directory not found: ${docforgeDir}`, 2);
  }
  const cleanTmp = !args.keep_tmp;
  const result = finishDocforge(docforgeDir, { cleanTmp });
  const cleaned = result.cleaned_dirs.length > 0 ? result.cleaned_dirs.join(", ") : "none";
  console.log(`finish  ensured ${path.join(docforgeDir, ".gitignore")}`);
  console.log(`finish  cleaned ephemeral scratch dirs: ${cleaned}`);
  return 0;
}
function usage() {
  console.log("usage: manage_manifest.js init --repo <path> --tier <spine|diligence|portfolio> [--shape <id>] [--platform <id>] [--framework <id>] [--concern <id>] [--audience <id>] | add --repo <path> --type <type> --id <id> --path <path> [--evidence <path:...|graph:...|user-confirmed:...>] | set --repo <path> --id <id> --status <status> | audit --repo <path> --id <id> --mode <cold-pass> --verdict <PASS|FAIL> --report <path> | status --repo <path> | finish --repo <path> [--keep-tmp]");
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
    return { init: cmdInit, add: cmdAdd, set: cmdSet, audit: cmdAudit, status: cmdStatus, reconcile: cmdReconcile, finish: cmdFinish }[args.command](args);
  } catch (error) {
    usage();
    return fail(error.message, 2);
  }
}
process.exit(main());
