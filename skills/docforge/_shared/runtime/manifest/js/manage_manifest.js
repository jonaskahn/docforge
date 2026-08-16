#!/usr/bin/env node
"use strict";
/** Create and maintain a Docforge manifest from the canonical catalog. */

const fs = require("fs");
const path = require("path");
const { dumpJson, ensureDocforgeGitignore, ensureGitignoredDir, fail, finishDocforge, loadManifest } = require("../../common/js/_util.js");
const { planLines } = require("../../common/js/plan.js");
const { computeScale, LAYOUT_BY_CLASS, LayoutTierError, layoutFor } = require("../../common/js/scale.js");
const { detect: detectProfiles, inventory: inventoryFiles } = require("../../catalog/js/detect_profiles.js");
const pf = require("../../common/js/provenance_frontmatter.js");
const store = require("../../common/js/provenance_store.js");
const queryCatalog = require("../../catalog/js/query_catalog.js");
const { SOURCES: GRAPH_SOURCES, resolveAllReady, resolveFirstReady } = require("../../graph/js/graph_source_registry.js");
const { reportFlowGraph } = require("../../graph/js/precheck_graph.js");

const SKILL_ROOT = path.resolve(fs.realpathSync(__dirname), "..", "..", "..");
const FLOW_INDEX_REL = path.join(".docforge", "flow-index.json");
const STATUSES = ["planned", "in_progress", "generated", "needs_review", "complete", "skipped", "retired"];
const WRITTEN = new Set(["generated", "needs_review", "complete"]);
const TRANSITIONS = {
  planned: new Set(["in_progress", "skipped"]),
  in_progress: new Set(["generated", "needs_review", "skipped"]),
  generated: new Set(["needs_review", "complete", "skipped"]),
  needs_review: new Set(["in_progress", "skipped"]),
  complete: new Set(["in_progress"]),
  skipped: new Set(["planned"]),
  retired: new Set(["planned"]),
};
const TOOL_VERSION = pf.GENERATOR_VERSION;
const MANIFEST_VERSION = "3.7";
const USER_CONFIRMED_TRIGGERS = new Set([
  "new-trust-boundary", "per-interaction-review", "regulated-workload",
  "high-criticality", "new-external-integration", "new-data-classification",
]);

function nowIso() {
  return new Date().toISOString().replace(/\.\d{3}Z$/, "+00:00");
}
const MANIFEST_HINT =
  "run migrate_metadata.js to re-register legacy manifests";

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
    retired: docs.filter((d) => d.status === "retired").length,
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
function makeDocument(definition, origins, evidence = [], catalogId = null, audiences = []) {
  // `definition` comes from the legacy-view catalog (bare filenames, kept
  // stable for --legacy CLI output); the manifest's scaffold_template must
  // be a skill-root-relative path so scaffold_docs.js can locate the file
  // after Phase 5 moved content artifacts out of one flat directory. For
  // dynamic types, `definition.id` is already the per-instance manifest id
  // by the time this runs, so callers pass the original catalog id
  // explicitly via `catalogId`.
  const detail = queryCatalog.loadType(catalogId || definition.id);
  const [primaryAudience, presentation] = queryCatalog.resolvePresentation(detail, audiences);
  const document = {
    id: definition.id,
    title: detail.title || definition.id.replace(/[-_]/g, " ").toLowerCase().replace(/\b\w/g, (c) => c.toUpperCase()),
    description: detail.summary || "",
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
    presentation: { primary_audience: primaryAudience, ...presentation },
    provenance: pf.scaffoldProvenance(definition.id, definition.path, {
      target_depth: definition.target_depth,
    }),
    audit: null,
  };
  if (detail.contract_revision !== undefined && detail.contract_revision !== null) {
    document.contract_revision = detail.contract_revision;
  }
  if (detail.nav_order !== undefined && detail.nav_order !== null) {
    document.nav_order = detail.nav_order;
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
function addAncestorIndexes(catalog, selected, audiences, skipIds = new Set()) {
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
        if (definition && !skipIds.has(definition.id) && !selectedPaths.has(candidate)) {
          selected.push(makeDocument(definition, [{ kind: "ancestor", id: child.id }], [], null, audiences));
          selectedPaths.add(candidate);
          changed = true;
        }
        parent = path.posix.dirname(parent);
      }
    }
  }
}
// Compact-layout fold: replace every selected document whose catalog record
// declares a `compact_group` with the group's single merged entry at its
// `compact_target`, members recorded on the entry so provenance and revise
// can trace them back. Strictly gated on `layout === "compact"` by the
// caller — a standard run never folds. Folded member ids are returned so
// ancestor-index computation skips resurrecting them.
// Order members by `compact_order`, then id. The id tiebreak is required:
// `compact_order` defaults to 0, so two members without an explicit order
// would otherwise have an unspecified relative order.
function compactMemberOrder(a, b) {
  return a[0] - b[0] || a[1].id.localeCompare(b[1].id);
}
function foldCompactGroups(catalog, selected, audiences) {
  const byId = new Map(catalog.documents.map((item) => [item.id, item]));
  const groups = new Map();
  const kept = [];
  for (const doc of selected) {
    const detail = queryCatalog.loadType(doc.id);
    const groupId = detail.compact_group;
    if (groupId) {
      if (!groups.has(groupId)) groups.set(groupId, []);
      groups.get(groupId).push([detail.compact_order || 0, doc]);
    } else {
      kept.push(doc);
    }
  }
  const foldedIds = new Set();
  for (const groupId of [...groups.keys()].sort()) {
    const members = groups.get(groupId);
    const definition = byId.get(groupId);
    if (!definition || (definition.selection || {}).mode !== "compact") {
      kept.push(...[...members].sort(compactMemberOrder).map(([, doc]) => doc));
      continue;
    }
    members.sort(compactMemberOrder);
    const merged = makeDocument(
      definition,
      [
        { kind: "tier", id: definition.selection.min_tier },
        { kind: "compact", id: groupId },
      ],
      [],
      null,
      audiences,
    );
    merged.compact_members = members.map(([, doc]) => doc.id);
    merged.requires = [...new Set(members.flatMap(([, doc]) => doc.requires || []))].sort();
    for (const [, doc] of members) foldedIds.add(doc.id);
    kept.push(merged);
  }
  return [kept, foldedIds];
}
function selectedStaticDocuments(catalog, repo, tier, profiles, layout = "standard") {
  const ranks = Object.fromEntries(catalog.tiers.map((item) => [item.id, item.order]));
  let selected = [];
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
    selected.push(makeDocument(definition, origins, evidence, null, profiles.audiences));
  }
  let foldedIds = new Set();
  if (layout === "compact") {
    [selected, foldedIds] = foldCompactGroups(catalog, selected, profiles.audiences);
  }
  addAncestorIndexes(catalog, selected, profiles.audiences, foldedIds);
  return selected.sort((a, b) => a.write_order - b.write_order || a.path.localeCompare(b.path) || a.id.localeCompare(b.id));
}
function parseArgs(argv) {
  if (!argv.length || argv.includes("-h") || argv.includes("--help")) return { help: true };
  const command = argv[0];
  const knownCommands = new Set(["init", "preview", "add", "set", "presentation", "audit", "status", "set-graph", "reconcile", "finish", "unmanaged", "retire"]);
  if (!knownCommands.has(command)) throw new Error(`unknown command: ${argv[0]}`);
  const repeatable = new Set(["shape", "platform", "framework", "concern", "audience", "overlay", "evidence", "doc"]);
  const boolean = new Set(["force", "keep-tmp", "reset", "dry-run", "json"]);
  const allowed = {
    init: new Set(["repo", "tier", "scale-class", "layout", "shape", "platform", "framework", "concern", "audience", "overlay", "name", "force", "graph-provider"]),
    preview: new Set(["repo", "tier", "layout", "scale-class", "shape", "platform", "framework", "concern", "audience", "json"]),
    add: new Set(["repo", "type", "id", "path", "title", "evidence"]),
    set: new Set(["repo", "id", "status"]),
    presentation: new Set(["repo", "id", "primary-audience", "code", "related-docs", "repository-paths", "reset"]),
    audit: new Set(["repo", "id", "mode", "verdict", "report"]),
    status: new Set(["repo"]),
    "set-graph": new Set(["repo", "provider", "force"]),
    reconcile: new Set(["repo", "tier", "scale-class", "layout", "shape", "platform", "framework", "concern", "audience"]),
    finish: new Set(["repo", "keep-tmp"]),
    unmanaged: new Set(["repo", "action", "path", "dry-run"]),
    retire: new Set(["repo", "doc", "mode", "dry-run"]),
  }[command];
  const result = { command, shape: [], platform: [], framework: [], concern: [], audience: [], overlay: [], evidence: [], doc: [] };
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
function resolveGraphLock(repo, provider) {
  if (provider) {
    const known = new Set(GRAPH_SOURCES.map((s) => s.name));
    if (!known.has(provider)) {
      throw new Error(`unknown graph provider: ${provider}; expected one of: ${[...known].sort().join(", ")}`);
    }
    const readyNames = new Set(resolveAllReady(repo, "code_graph").map(([s]) => s.name));
    if (!readyNames.has(provider)) {
      throw new Error(`graph provider ${provider} is not ready in this repo`);
    }
    return { provider, flow: reportFlowGraph(repo), locked_at: nowIso() };
  }
  const [source] = resolveFirstReady(repo, "code_graph");
  if (!source) return null;
  return { provider: source.name, flow: reportFlowGraph(repo), locked_at: nowIso() };
}
// Build the `project.scale` record. Omitted flags adopt detection; any
// explicit flag records `decided_by: "user"` with `detected_class` preserved
// so a later run never silently re-classifies an override. `files` and
// `detections` let a caller that already walked the repo avoid a second walk.
//
// `tier` gates the layout through `layoutFor`: an explicit compact pick at
// Portfolio throws LayoutTierError, and a detected compact layout there is
// forced to standard as `decided_by: "tier-constraint"`.
function resolveScale(repo, scaleClass, layout, files = null, detections = null, tier = "diligence") {
  const detected = computeScale(repo, files, detections);
  if (!scaleClass && !layout) {
    const resolved = layoutFor(tier, detected.suggested_layout, { explicit: false });
    const record = {
      class: detected.class,
      layout: resolved.layout,
      decided_by: resolved.decided_by,
      decided_at: nowIso(),
      signals: detected.signals,
    };
    if (resolved.decided_by === "tier-constraint") record.detected_class = detected.class;
    return record;
  }
  const chosenClass = scaleClass || detected.class;
  const resolved = layoutFor(tier, layout || LAYOUT_BY_CLASS[chosenClass], { explicit: Boolean(layout) });
  // Either flag being present makes this a user decision; the tier can still
  // override the layout it implied, and that override is what gets recorded.
  return {
    class: chosenClass,
    layout: resolved.layout,
    detected_class: detected.class,
    decided_by: resolved.decided_by === "tier-constraint" ? "tier-constraint" : "user",
    decided_at: nowIso(),
    signals: detected.signals,
  };
}
function cmdInit(args) {
  required(args, ["repo", "tier"]);
  if (args.overlay.length) return fail("--overlay is unsupported in Docforge 2.0; use --shape, --platform, --framework, --concern, or --audience", 2);
  if (!["spine", "diligence", "portfolio"].includes(args.tier)) return fail(`invalid tier: ${args.tier}`, 2);
  if (args.scale_class && !["small", "medium", "large"].includes(args.scale_class)) return fail(`invalid scale class: ${args.scale_class}`, 2);
  if (args.layout && !["compact", "standard"].includes(args.layout)) return fail(`invalid layout: ${args.layout}`, 2);
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
  // One walk feeds both the discovery record and the scale record.
  const walked = inventoryFiles(fs.realpathSync(args.repo));
  const discovery = detectProfiles(fs.realpathSync(args.repo), true, walked);
  let projectScale;
  try {
    projectScale = resolveScale(args.repo, args.scale_class, args.layout, walked, discovery, args.tier);
  } catch (error) {
    if (error instanceof LayoutTierError) return fail(error.message, 2);
    throw error;
  }
  const docs = selectedStaticDocuments(catalog, args.repo, args.tier, profiles, projectScale.layout);
  const manifest = {
    version: MANIFEST_VERSION,
    generated_at: nowIso(),
    project: {
      name: args.name || path.basename(path.resolve(args.repo)),
      root: path.resolve(args.repo),
      tier: args.tier,
      scale: projectScale,
      profiles,
      provenance_storage: store.STORAGE_JSON,
      unmanaged_docs: [],
    },
    discovery,
    discovery_gate: null,
    documents: docs,
    metadata: {},
  };
  let graphLock;
  try {
    graphLock = resolveGraphLock(args.repo, args.graph_provider);
  } catch (error) {
    return fail(error.message, 2);
  }
  if (graphLock) manifest.graph = graphLock;
  saveManifest(args.repo, manifest);
  console.log(`Wrote ${target} — tier ${args.tier}, ${docs.length} static documents planned.`);
  if (graphLock) {
    console.log(`Locked graph provider: ${graphLock.provider} (flow: ${graphLock.flow})`);
  } else {
    console.log("No graph provider ready yet — run `set-graph` once a code graph is built.");
  }
  console.log("");
  for (const line of planLines(args.repo, manifest, path.join(args.repo, ".docforge", "flow-index.json"))) {
    console.log(line);
  }
  return 0;
}
function cmdSetGraph(args) {
  required(args, ["repo"]);
  try {
    const manifest = loadManifest(manifestPath(args.repo), { unsupportedHint: MANIFEST_HINT });
    let lock;
    try {
      lock = resolveGraphLock(args.repo, args.provider);
    } catch (error) {
      return fail(error.message, 2);
    }
    if (!lock) return fail("no graph provider is ready in this repo", 2);
    const existing = manifest.graph;
    if (existing && existing.provider !== lock.provider && !args.force) {
      return fail(
        `graph provider is locked to ${existing.provider} for this session (locked_at ${existing.locked_at}); pass --force to relock to ${lock.provider}`,
        2,
      );
    }
    let verb = "Locked";
    if (existing) {
      verb = existing.provider === lock.provider ? "Updated" : "Relocked";
      if (existing.provider === lock.provider) lock.locked_at = existing.locked_at;
    }
    manifest.graph = lock;
    saveManifest(args.repo, manifest);
    console.log(`${verb} graph provider: ${lock.provider} (flow: ${lock.flow})`);
    return 0;
  } catch (error) {
    return fail(error.message, 2);
  }
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
    manifest.documents.push(makeDocument(actual, origins, evidence, definition.id, manifest.project.profiles.audiences));
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
function catalogIdForDocument(catalog, doc) {
  if (doc.id === doc.type) return doc.id;
  for (const candidate of catalog.documents) {
    if (candidate.id === doc.id) return candidate.id;
    if (candidate.type === doc.type && (candidate.selection || {}).mode === "dynamic") {
      return candidate.id;
    }
  }
  return null;
}

function effectivePresentation(catalogId, audiences, override = null) {
  let detail = queryCatalog.loadType(catalogId);
  if (override) detail = { ...detail, presentation: { ...(detail.presentation || {}), ...override } };
  const [primaryAudience, presentation] = queryCatalog.resolvePresentation(detail, audiences);
  return { primary_audience: primaryAudience, ...presentation };
}

function demoteForPresentationChange(doc) {
  if (["generated", "needs_review", "complete"].includes(doc.status)) {
    doc.status = "in_progress";
    doc.audit = null;
  }
}

function syncContractRevisions(catalog, docs) {
  // Refresh catalog-owned metadata on kept documents and demote written
  // documents whose content-contract revision drifted (so a revise run
  // re-grounds them even when source provenance is FRESH).
  const contractUpdated = [];
  for (const doc of docs) {
    const catalogId = catalogIdForDocument(catalog, doc);
    if (catalogId === null) continue;
    const detail = queryCatalog.loadType(catalogId);
    doc.title = detail.title || doc.title;
    doc.description = detail.summary || doc.description || "";
    doc.scaffold_template = detail.template_file;
    doc.instruction_file = detail.instruction_file === undefined ? null : detail.instruction_file;
    if (detail.target_depth !== undefined) doc.target_depth = detail.target_depth;
    if (detail.write_order !== undefined) doc.write_order = detail.write_order;
    if (detail.nav_order !== undefined && detail.nav_order !== null) doc.nav_order = detail.nav_order;
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

function syncPresentations(catalog, docs, audiences) {
  const updated = [];
  for (const doc of docs) {
    const catalogId = catalogIdForDocument(catalog, doc);
    if (catalogId === null) continue;
    const resolved = effectivePresentation(catalogId, audiences, doc.presentation_override || null);
    if (!("presentation" in doc)) {
      doc.presentation = resolved;
      continue;
    }
    if (JSON.stringify(doc.presentation) !== JSON.stringify(resolved)) {
      doc.presentation = resolved;
      demoteForPresentationChange(doc);
      updated.push(doc.id);
    }
  }
  return updated;
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
  const currentScale = manifest.project.scale || {};
  const requestedLayout = args.layout
    || (args.scale_class ? LAYOUT_BY_CLASS[args.scale_class] : null)
    || currentScale.layout
    || "standard";
  // Moving to portfolio drops a compact manifest to standard; the folded
  // members return as planned and the merged entry becomes a retire candidate
  // through the ordinary compact->standard path below.
  let newLayout;
  let layoutConstraint;
  try {
    ({ layout: newLayout, decided_by: layoutConstraint } = layoutFor(newTier, requestedLayout, { explicit: Boolean(args.layout) }));
  } catch (error) {
    if (error instanceof LayoutTierError) return fail(error.message, 2);
    throw error;
  }
  const tierForcedLayout = layoutConstraint === "tier-constraint";
  const raw = {};
  for (const dimension of PROFILE_DIMENSIONS) {
    const singular = dimension === "audiences" ? "audience" : dimension.slice(0, -1);
    const values = [...(args[singular] || [])];
    raw[dimension] = values.length === 1 && values[0] === "none"
      ? []
      : (values.length ? values : (manifest.project.profiles[dimension] || []));
  }
  let profiles;
  try {
    profiles = normalizeProfiles(catalog, raw);
  } catch (error) {
    return fail(error.message, 2);
  }
  const selected = selectedStaticDocuments(catalog, args.repo, newTier, profiles, newLayout);
  const selectedIds = new Set(selected.map((doc) => doc.id));
  const kept = [];
  const removed = [];
  const retire = [];
  const keptIds = new Set();
  for (const doc of manifest.documents) {
    const origins = ((doc.selection || {}).origins) || [];
    const isDynamic = origins.some((origin) => origin.kind === "dynamic");
    if (selectedIds.has(doc.id)) {
      if (doc.status === "retired") {
        doc.status = "planned";
        doc.audit = null;
        delete doc.retired_at;
        delete doc.retired_destination;
      }
      kept.push(doc);
      keptIds.add(doc.id);
    } else if (isDynamic || doc.status !== "planned") {
      if (!isDynamic && WRITTEN.has(doc.status)) retire.push(doc.id);
      kept.push(doc);
      keptIds.add(doc.id);
    } else {
      removed.push(doc.id);
    }
  }
  const added = selected.filter((doc) => !keptIds.has(doc.id));
  const contractUpdated = syncContractRevisions(catalog, kept);
  const presentationUpdated = syncPresentations(catalog, kept, profiles.audiences);
  const oldTier = manifest.project.tier;
  manifest.documents = [...kept, ...added];
  manifest.documents.sort((a, b) => a.write_order - b.write_order || a.path.localeCompare(b.path) || a.id.localeCompare(b.id));
  manifest.project.tier = newTier;
  manifest.project.profiles = profiles;
  if (args.scale_class || args.layout || tierForcedLayout) {
    let scaleRecord;
    if (currentScale.class) {
      scaleRecord = { ...currentScale };
    } else {
      // A pre-3.5 manifest reconciled before migrate has no usable prior
      // record. Detect a complete one rather than emit a record missing the
      // schema-required `class`.
      scaleRecord = resolveScale(args.repo, args.scale_class, args.layout);
    }
    const oldClass = scaleRecord.class;
    const oldLayout = scaleRecord.layout || "standard";
    if (args.scale_class && args.scale_class !== oldClass) {
      scaleRecord.class = args.scale_class;
      // A class change carries its class-default layout unless the user also
      // named a layout.
      if (!args.layout) scaleRecord.layout = LAYOUT_BY_CLASS[args.scale_class];
    }
    if (args.layout && args.layout !== oldLayout) {
      scaleRecord.layout = args.layout;
    }
    if (tierForcedLayout) {
      // The tier overrides whatever layout the flags or the manifest implied;
      // record that as the reason rather than as a user pick.
      scaleRecord.layout = newLayout;
    }
    scaleRecord.decided_by = tierForcedLayout ? "tier-constraint" : "user";
    scaleRecord.decided_at = nowIso();
    const detected = computeScale(args.repo);
    scaleRecord.detected_class = detected.class;
    scaleRecord.signals = detected.signals;
    manifest.project.scale = scaleRecord;
    if (oldClass !== scaleRecord.class) {
      console.log(`  scale class: ${oldClass} -> ${scaleRecord.class}`);
    }
    if (oldLayout !== scaleRecord.layout) {
      console.log(`  layout: ${oldLayout} -> ${scaleRecord.layout}`);
    }
  }
  saveManifest(args.repo, manifest);
  console.log(`Reconcile ${args.repo}:`);
  console.log(`  tier: ${oldTier} -> ${newTier}`);
  for (const dimension of PROFILE_DIMENSIONS) {
    console.log(`  ${dimension}: ${profiles[dimension].join(", ") || "(none)"}`);
  }
  const countParts = [];
  if (added.length) countParts.push(`${added.length} add`);
  if (removed.length) countParts.push(`${removed.length} removed-planned`);
  if (retire.length) countParts.push(`${retire.length} retire`);
  if (contractUpdated.length) countParts.push(`${contractUpdated.length} contract-updated`);
  if (presentationUpdated.length) countParts.push(`${presentationUpdated.length} presentation-updated`);
  console.log(`  counts: ${countParts.join(", ") || "no change"}`);
  if (added.length) console.log(`  added: ${added.map((doc) => doc.id).sort().join(", ")}`);
  if (removed.length) console.log(`  removed-planned: ${removed.sort().join(", ")}`);
  if (retire.length) console.log(`  retire: ${retire.sort().join(", ")} (written, out of scope — approve the retire step to move or delete)`);
  if (contractUpdated.length) console.log(`  contract-updated: ${contractUpdated.sort().join(", ")}`);
  if (presentationUpdated.length) console.log(`  presentation-updated: ${presentationUpdated.sort().join(", ")}`);
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
    if (!(TRANSITIONS[old] || new Set()).has(args.status)) return fail(`invalid status transition for ${args.id}: ${old} -> ${args.status}`, 2);
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
function cmdPresentation(args) {
  required(args, ["repo", "id"]);
  try {
    const manifest = loadManifest(manifestPath(args.repo), { unsupportedHint: MANIFEST_HINT });
    const doc = findDocument(manifest, args.id);
    const catalog = loadCatalog();
    const catalogId = catalogIdForDocument(catalog, doc);
    if (catalogId === null) throw new Error(`catalog definition not found for document: ${args.id}`);
    if (args.reset) {
      if (args.primary_audience || args.code || args.related_docs || args.repository_paths) {
        return fail("--reset cannot be combined with presentation values", 2);
      }
      delete doc.presentation_override;
    } else {
      const override = {};
      for (const [field, value] of Object.entries({
        primary_audience: args.primary_audience,
        code: args.code,
        related_docs: args.related_docs,
        repository_paths: args.repository_paths,
      })) {
        if (value !== undefined) override[field] = value;
      }
      if (!Object.keys(override).length) return fail("set at least one presentation value or pass --reset", 2);
      const audienceIds = new Set(catalog.profiles.audiences.map((item) => item.id));
      if (override.primary_audience && !audienceIds.has(override.primary_audience)) {
        return fail(`unknown audience: ${override.primary_audience}`, 2);
      }
      for (const [field, allowed] of Object.entries(queryCatalog.PRESENTATION_VALUES)) {
        if (field in override && !allowed.has(override[field])) return fail(`invalid ${field}: ${override[field]}`, 2);
      }
      doc.presentation_override = { ...(doc.presentation_override || {}), ...override };
    }
    const resolved = effectivePresentation(catalogId, manifest.project.profiles.audiences, doc.presentation_override || null);
    const changed = JSON.stringify(doc.presentation) !== JSON.stringify(resolved);
    doc.presentation = resolved;
    if (changed) demoteForPresentationChange(doc);
    saveManifest(args.repo, manifest);
    console.log(`Presentation ${args.id}: ${changed ? "updated" : "unchanged"}.`);
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
    if (manifest.graph) {
      console.log(`  graph: ${manifest.graph.provider} (flow: ${manifest.graph.flow})`);
    }
    console.log();
    for (const doc of manifest.documents) {
      const verdict = doc.audit ? doc.audit.verdict : "-";
      console.log(`  ${doc.status.padEnd(12)}  ${verdict.padEnd(4)}  ${doc.id.padEnd(28)}  ${doc.path}`);
    }
    const c = manifest.metadata;
    console.log();
    console.log(`${c.total_documents} documents: planned=${c.planned} in_progress=${c.in_progress} generated=${c.generated} needs_review=${c.needs_review} complete=${c.complete} skipped=${c.skipped} retired=${c.retired || 0}`);
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
// Move out-of-scope written documents to a git-ignored obsolete location
// (default) or delete them, marking the manifest entry `retired` — the entry
// itself is always preserved. A file operation: never under `--auto-accept`,
// always an explicitly approved step after `reconcile` reports the delta.
function cmdRetire(args) {
  required(args, ["repo", "doc", "mode"]);
  if (!["obsolete", "delete"].includes(args.mode)) return fail(`invalid retire mode: ${args.mode}`, 2);
  let manifest;
  try {
    manifest = loadManifest(manifestPath(args.repo), { unsupportedHint: MANIFEST_HINT });
  } catch (error) {
    return fail(error.message, 2);
  }
  const year = String(new Date().getUTCFullYear());
  if (!args.dry_run) ensureDocforgeGitignore(path.join(args.repo, ".docforge"));
  let movedAny = false;
  for (const docId of args.doc) {
    let doc;
    try {
      doc = findDocument(manifest, docId);
    } catch (error) {
      return fail(error.message, 2);
    }
    if (doc.status === "retired") {
      console.log(`retire  ${docId}: already retired; no changes.`);
      continue;
    }
    if (!WRITTEN.has(doc.status)) {
      return fail(`${docId} has status ${doc.status}; only written documents can be retired`, 2);
    }
    const value = doc.path.replace(/\\/g, "/");
    const valueParts = value.split("/");
    let label;
    if (args.mode === "obsolete") {
      const targetParts = [".docforge", "obsolete", year, ...valueParts];
      const target = targetParts.join("/");
      label = `move ${value} -> ${target}`;
      if (args.dry_run) {
        console.log(`DRY RUN  retire ${docId}: ${label}`);
        continue;
      }
      const source = path.join(args.repo, ...valueParts);
      if (!fs.existsSync(source) || !fs.statSync(source).isFile()) {
        return fail(`file not found: ${value}`, 2);
      }
      const destination = path.join(args.repo, ...targetParts);
      if (fs.existsSync(destination)) return fail(`retire target already exists: ${target}`, 2);
      fs.mkdirSync(path.dirname(destination), { recursive: true });
      ensureGitignoredDir(path.join(args.repo, ".docforge", "obsolete", year));
      fs.renameSync(source, destination);
      doc.retired_destination = target;
    } else {
      label = `delete ${value}`;
      if (args.dry_run) {
        console.log(`DRY RUN  retire ${docId}: ${label}`);
        continue;
      }
      const source = path.join(args.repo, ...valueParts);
      if (fs.existsSync(source) && fs.statSync(source).isFile()) fs.unlinkSync(source);
    }
    doc.retired_at = nowIso();
    doc.status = "retired";
    doc.audit = null;
    movedAny = true;
    console.log(`retire  ${docId}: ${label} (status -> retired; entry preserved)`);
  }
  if (!args.dry_run && movedAny) saveManifest(args.repo, manifest);
  return 0;
}

const UNMANAGED_ROOTS = ["docs/", "docs-portfolio/"];
function unmanagedSource(rel) {
  for (const root of UNMANAGED_ROOTS) {
    if (!rel.startsWith(root)) continue;
    const rest = rel.slice(root.length);
    if (!rest) continue;
    if (rest.endsWith(".md") || rest.endsWith(".mdx")) return root;
  }
  return null;
}
function validateUnmanagedPath(repo, value) {
  validateRelativePath(value);
  const root = unmanagedSource(value);
  if (!root) {
    throw new Error(`unmanaged path must be a .md/.mdx file under ${UNMANAGED_ROOTS.join(" or ")}: ${value}`);
  }
  if (!fs.existsSync(path.join(repo, ...value.split("/"))) || !fs.statSync(path.join(repo, ...value.split("/"))).isFile()) {
    throw new Error(`file not found: ${value}`);
  }
  return value.replace(/\\/g, "/");
}
function cmdUnmanaged(args) {
  required(args, ["repo", "action"]);
  if (!["list", "add", "remove", "archive"].includes(args.action)) {
    return fail(`unknown unmanaged action: ${args.action}`, 2);
  }
  try {
    const manifest = loadManifest(manifestPath(args.repo), {
      unsupportedHint: MANIFEST_HINT,
    });
    const entries = manifest.project.unmanaged_docs || [];
    const byPath = new Map(entries.map((entry) => [entry.path, entry]));
    if (args.action === "list") {
      if (!entries.length) {
        console.log("unmanaged  none");
        return 0;
      }
      for (const entry of entries) console.log(`unmanaged  ${entry.path}  (since ${entry.decided_at})`);
      return 0;
    }
    if (!args.path) return fail(`unmanaged ${args.action} requires --path`, 2);
    if (args.action === "add" || args.action === "archive") {
      const value = validateUnmanagedPath(args.repo, args.path);
      const tracked = new Set(manifest.documents.map((doc) => doc.path).filter(Boolean));
      if (tracked.has(value)) {
        return fail(`${value} is a tracked manifest document; unmanaged is for docs Docforge does not own`, 2);
      }
      if (args.action === "add") {
        if (byPath.has(value)) {
          console.log(`unmanaged  ${value} already self-managed; no changes.`);
          return 0;
        }
        entries.push({ path: value, decided_at: nowIso() });
        saveManifest(args.repo, manifest);
        console.log(`unmanaged  ${value} -> self-managed (never tracked, never re-asked)`);
        return 0;
      }
      const parts = value.split("/");
      const archiveRoot = parts[0] === "docs-portfolio" ? "docs-portfolio" : "docs";
      const target = [archiveRoot, "_archive", String(new Date().getUTCFullYear()), ...parts.slice(1)].join("/");
      if (args.dry_run) {
        console.log(`DRY RUN  move ${value} -> ${target}`);
        return 0;
      }
      if (fs.existsSync(path.join(args.repo, ...target.split("/")))) {
        return fail(`archive target already exists: ${target}`, 2);
      }
      fs.mkdirSync(path.dirname(path.join(args.repo, ...target.split("/"))), { recursive: true });
      fs.renameSync(path.join(args.repo, ...value.split("/")), path.join(args.repo, ...target.split("/")));
      entries.push({ path: target, decided_at: nowIso() });
      saveManifest(args.repo, manifest);
      console.log(`unmanaged  ${value} -> ${target} (archived)`);
      return 0;
    }
    if (args.action === "remove") {
      if (!byPath.has(args.path)) {
        console.log(`unmanaged  ${args.path} not in list; no changes.`);
        return 0;
      }
      manifest.project.unmanaged_docs = entries.filter((entry) => entry.path !== args.path);
      saveManifest(args.repo, manifest);
      console.log(`unmanaged  ${args.path} -> removed from list (file untouched)`);
      return 0;
    }
    return fail(`unknown unmanaged action: ${args.action}`, 2);
  } catch (error) {
    return fail(error.message, 2);
  }
}
// The `[dimension, value]` pairs this invocation actually selected.
function selectionValues(args) {
  const pairs = [];
  for (const [dimension, singular] of [
    ["shapes", "shape"], ["platforms", "platform"], ["frameworks", "framework"],
    ["concerns", "concern"], ["audiences", "audience"],
  ]) {
    for (const value of args[singular] || []) pairs.push([dimension, value]);
  }
  return pairs;
}
// Report how large a tree a scope would produce, without writing anything.
//
// Intake needs this before the confirmation gate: a user picking profiles and
// audiences has no way to know that most dimensions cost nothing while one
// audience can carry a third of the tree. Read-only — no manifest, no
// directories, no side effects of any kind.
function cmdPreview(args) {
  const catalog = loadCatalog();
  let profiles;
  try {
    profiles = normalizeProfiles(catalog, {
      shapes: args.shape, platforms: args.platform, frameworks: args.framework,
      concerns: args.concern,
      audiences: (args.audience && args.audience.length) ? args.audience : ["engineers", "beginners"],
    });
  } catch (error) {
    return fail(error.message, 2);
  }
  const count = (layout, drop) => {
    const trimmed = { ...profiles };
    if (drop) trimmed[drop[0]] = profiles[drop[0]].filter((v) => v !== drop[1]);
    return selectedStaticDocuments(catalog, args.repo, args.tier, trimmed, layout).length;
  };
  const standardCount = count("standard");
  const report = { tier: args.tier, standard_count: standardCount };
  try {
    const resolved = layoutFor(args.tier, "compact", { explicit: true });
    report.compact_count = count(resolved.layout);
  } catch (error) {
    if (!(error instanceof LayoutTierError)) throw error;
    report.compact_count = null;
    report.compact_unavailable = error.message;
  }
  // Ablation, not origin-counting: "how many documents disappear if this value
  // is dropped" is the number a user weighing a choice actually wants, and it
  // stays correct when several selections claim the same document.
  let layout = args.layout || (report.compact_count !== null ? "compact" : "standard");
  if (layout === "compact" && report.compact_count === null) layout = "standard";
  const baseline = count(layout);
  report.layout = layout;
  report.count = baseline;
  const attribution = [];
  for (const [dimension, value] of selectionValues(args)) {
    if (!profiles[dimension].includes(value)) continue;
    attribution.push({ dimension, value, documents: baseline - count(layout, [dimension, value]) });
  }
  attribution.sort((a, b) => (b.documents - a.documents)
    || a.dimension.localeCompare(b.dimension) || a.value.localeCompare(b.value));
  report.attribution = attribution;

  if (args.json) {
    process.stdout.write(dumpJson(report));
    return 0;
  }
  console.log(`Preview ${args.repo} — tier: ${args.tier}`);
  console.log(`  standard: ${standardCount} documents`);
  if (report.compact_count === null) {
    console.log(`  compact:  unavailable — ${report.compact_unavailable}`);
  } else {
    console.log(`  compact:  ${report.compact_count} documents`);
  }
  console.log(`  projected (${layout}): ${baseline} documents`);
  if (attribution.length) {
    console.log("  attribution (documents lost if the value is dropped):");
    for (const item of attribution) {
      const share = (baseline && item.documents)
        ? ` — ${Math.round(100 * item.documents / baseline)}% of the tree` : "";
      console.log(`    ${item.dimension.slice(0, -1)}=${item.value}: ${item.documents}${share}`);
    }
  }
  console.log("  (read-only: nothing was written)");
  return 0;
}
function usage() {
  console.log("usage: manage_manifest.js init --repo <path> --tier <spine|diligence|portfolio> [--scale-class <small|medium|large>] [--layout <compact|standard>] [--shape <id>] [--platform <id>] [--framework <id>] [--concern <id>] [--audience <id>] [--graph-provider <id>] | preview --repo <path> --tier <spine|diligence|portfolio> [--layout <compact|standard>] [--shape <id>] [--platform <id>] [--framework <id>] [--concern <id>] [--audience <id>] [--json] | add --repo <path> --type <type> --id <id> --path <path> [--evidence <path:...|graph:...|user-confirmed:...>] | set --repo <path> --id <id> --status <status> | presentation --repo <path> --id <id> [--primary-audience <id>] [--code <mode>] [--related-docs <mode>] [--repository-paths <mode>] [--reset] | audit --repo <path> --id <id> --mode <cold-pass> --verdict <PASS|FAIL> --report <path> | status --repo <path> | set-graph --repo <path> [--provider <id>] [--force] | reconcile --repo <path> [--tier <spine|diligence|portfolio>] [--scale-class <small|medium|large>] [--layout <compact|standard>] [--shape <id>] [--platform <id>] [--framework <id>] [--concern <id>] [--audience <id>] | unmanaged --repo <path> --action <list|add|remove|archive> [--path <rel>] [--dry-run] | retire --repo <path> --doc <id> [--doc <id> ...] --mode <obsolete|delete> [--dry-run] | finish --repo <path> [--keep-tmp]");
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
    return { init: cmdInit, preview: cmdPreview, add: cmdAdd, set: cmdSet, presentation: cmdPresentation, audit: cmdAudit, status: cmdStatus, "set-graph": cmdSetGraph, reconcile: cmdReconcile, finish: cmdFinish, unmanaged: cmdUnmanaged, retire: cmdRetire }[args.command](args);
  } catch (error) {
    usage();
    return fail(error.message, 2);
  }
}
process.exit(main());
