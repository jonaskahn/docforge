#!/usr/bin/env node
"use strict";
/** Harvest, rank, revise, organize, and render Docforge's repository flow index.
 *
 * Understand Anything JSON is read directly. GitNexus is consumed through a
 * deterministic interchange JSON the agent materializes at
 * `.docforge/tmp/gitnexus-flows.json` (from the GitNexus MCP or the offline
 * lbug reader — never a CLI flag). CodeGraph-only repositories seed derived
 * candidates through `import --analysis` from the agent's flow analysis.
 *
 *   node flow_index.js harvest --repo <repo>
 *   node flow_index.js revise --repo <repo>
 *   node flow_index.js organize emit --repo <repo>
 *   node flow_index.js organize apply --repo <repo> --organization <json>
 *   node flow_index.js update --repo <repo> --id <flow-id> [--priority main|deferred] [--status placeholder|skipped] [--summary <text>] [--written]
 *   node flow_index.js import --repo <repo> --analysis <flow-analysis.json> [--main-limit <n>]
 *   node flow_index.js render --repo <repo>
 */

const fs = require("fs");
const path = require("path");
const crypto = require("crypto");
const { spawnSync } = require("child_process");
const { fail, readJson } = require("../../common/js/_util.js");
const pf = require("../../common/js/provenance_frontmatter.js");
const store = require("../../common/js/provenance_store.js");
const { ensureTmpDirGitignored } = require("../../graph/js/graph_storage.js");
const {
  FLOW_INDEX_VERSION: INDEX_VERSION,
  SUPPORTED_FLOW_INDEX_VERSIONS: SUPPORTED_INDEX_VERSIONS,
  upgradeIndex,
} = require("../../common/js/flow_index_schema.js");

const INDEX_REL = path.join(".docforge", "flow-index.json");
const TMP_REL = path.join(".docforge", "tmp");
const ORG_PACK_REL = path.join(TMP_REL, "flow-organization-pack.json");
const GITNEXUS_FLOWS_REL = path.join(TMP_REL, "gitnexus-flows.json");
const DERIVED_FLOW_GRAPH_REL = path.join(TMP_REL, "flow-graph.json");
const UA_DIRS = [".ua", ".understand-anything"];
const BARE_VERBS = new Set([
  "get", "save", "create", "update", "delete", "execute", "init", "count",
  "publish", "verify", "connect", "archive", "resend", "authorize", "send",
  "post", "put", "patch", "run", "start", "handle", "process", "dispatch",
  "receive", "consume", "track", "aggregate",
]);
const ENTRY_WORDS = /^(?:[Aa]ggregate|[Tt]rack|[Pp]ublish|[Dd]ispatch|[Ee]xecute|[Rr]un|[Ss]tart|[Rr]eceive|[Pp]rocess|[Cc]onsume|[Hh]andle|[Cc]reate|[Uu]pdate|[Dd]elete|[Ss]ave|[Gg]et|[Pp]ost|[Pp]ut|[Pp]atch|[Ss]end)(?:[A-Z0-9_]|$)/;
const CORE_ENTRY_WORDS = /^(?:[Aa]ggregate|[Tt]rack|[Pp]ublish|[Dd]ispatch|[Ee]xecute|[Rr]un|[Ss]tart|[Rr]eceive|[Pp]rocess|[Cc]onsume|[Hh]andle)(?:[A-Z0-9_]|$)/;
const SURFACE_WORDS = /(controller|handler|processor|consumer|listener|worker|job|command|aggregator)$/i;
const PATH_WORDS = /(controllers?|handlers?|processors?|consumers?|workers?|jobs?|commands?|aggregators?|routes?|endpoints?)/i;
const FAMILY_RE = /^[a-z0-9][a-z0-9-]*$/;
const FLOW_ID_RE = /^flow-[a-z0-9][a-z0-9-]*$/;
const SLUG_RE = /^[a-z0-9][a-z0-9-]*$/;

function nowIso() {
  return new Date().toISOString().replace(/\.\d{3}Z$/, "+00:00");
}
function findUa(repo, name) {
  for (const directory of UA_DIRS) {
    const target = path.join(repo, directory, name);
    if (fs.existsSync(target) && fs.statSync(target).isFile()) return target;
  }
  return null;
}
function slugify(value) {
  return value.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "").slice(0, 80) || "unnamed-flow";
}
function splitSymbolId(value) {
  if (!value) return [null, null];
  const parts = String(value).split(":");
  return parts.length >= 3 ? [parts[1], parts[parts.length - 1]] : [null, parts[parts.length - 1]];
}
function moduleFromPath(filePath) {
  if (!filePath) return null;
  const normalized = String(filePath).replace(/\\/g, "/");
  let match = normalized.match(/(?:^|\/)(?:src\/)?modules\/([^/]+)/);
  if (match) return slugify(match[1]);
  match = normalized.match(/(?:^|\/)src\/([^/]+)\//);
  if (match) {
    const segment = match[1].toLowerCase();
    if (!["lib", "utils", "common", "shared", "helpers", "types"].includes(segment)) {
      return slugify(segment);
    }
  }
  return null;
}
function baseSlugFor(row) {
  const name = String(row.name || "");
  const base = slugify(name);
  const symbol = String((row.entry_ref && row.entry_ref.symbol) || name);
  const symbolSlug = slugify(symbol);
  if (BARE_VERBS.has(base) || BARE_VERBS.has(symbolSlug)) {
    const moduleName = moduleFromPath(row.entry_ref && row.entry_ref.filePath);
    if (moduleName) return `${moduleName}-${base}`;
  }
  return base;
}
function inferKind(signature, filePath = null) {
  const text = `${signature} ${filePath || ""}`.toLowerCase();
  if (/\b(get|post|put|patch|delete)\b|\/api\/|controller|handler|route/.test(text)) return "http";
  if (/queue|consumer|listener/.test(text)) return "queue";
  if (/cron|schedule|job/.test(text)) return "schedule";
  if (/command|cli/.test(text)) return "cli";
  if (/screen|view|component|page/.test(text)) return "ui";
  return "internal";
}
function normalizeKind(value, signature, filePath = null) {
  const aliases = {
    http: "http", api: "http", web: "http",
    queue: "queue", event: "queue", message: "queue",
    schedule: "schedule", scheduled: "schedule", cron: "schedule", timer: "schedule",
    cli: "cli", command: "cli", ui: "ui", screen: "ui", internal: "internal",
  };
  return aliases[String(value || "").toLowerCase()] || inferKind(signature, filePath);
}
function candidate({ name, kind, signature, filePath, symbol, area, evidence, confidence = "candidate", steps = 0, boundaries = 0 }) {
  return {
    name,
    entry_ref: { kind, signature, filePath: filePath || null, symbol: symbol || null },
    area: area || "Unclassified",
    evidence: [evidence],
    confidence,
    reach: { steps: Number(steps || 0), boundaries: Number(boundaries || 0), churn: 0 },
  };
}
function harvestUaDomain(target) {
  const doc = readJson(target);
  const nodes = doc.nodes || [];
  const edges = doc.edges || [];
  const byId = new Map(nodes.filter((node) => node && typeof node === "object").map((node) => [node.id, node]));
  const domainFor = new Map();
  const domainIdFor = new Map();
  const stepFor = new Map();
  for (const edge of edges) {
    if (!edge || typeof edge !== "object") continue;
    if (edge.type === "contains_flow") {
      const domain = byId.get(edge.source) || {};
      domainFor.set(edge.target, domain.name || "Unclassified");
      domainIdFor.set(edge.target, edge.source);
    } else if (edge.type === "flow_step") {
      const step = byId.get(edge.target);
      if (step) {
        if (!stepFor.has(edge.source)) stepFor.set(edge.source, []);
        stepFor.get(edge.source).push(step);
      }
    }
  }
  const rows = [];
  for (const flow of nodes) {
    if (!flow || flow.type !== "flow") continue;
    const meta = flow.domainMeta || {};
    const steps = stepFor.get(flow.id) || [];
    const first = steps[0] || {};
    const signature = String(meta.entryPoint || flow.name || flow.id);
    const domainId = domainIdFor.get(flow.id);
    const crosses = edges.some((edge) => edge && edge.type === "cross_domain" && (edge.source === domainId || edge.target === domainId));
    rows.push(candidate({
      name: String(flow.name || signature),
      kind: normalizeKind(meta.entryType, signature, first.filePath),
      signature,
      filePath: first.filePath,
      symbol: null,
      area: domainFor.get(flow.id),
      evidence: { provider: "understand-anything", artifact: target, nodeId: flow.id },
      confidence: "confirmed",
      steps: steps.length,
      boundaries: crosses ? 1 : 0,
    }));
  }
  return rows;
}
function harvestUaKnowledge(target) {
  const doc = readJson(target);
  const nodes = (doc.nodes || []).filter((node) => node && typeof node === "object");
  const areaById = new Map();
  for (const layer of doc.layers || []) {
    if (!layer || typeof layer !== "object") continue;
    const layerName = String(layer.name || "");
    if (!["presentation", "api", "application", "service"].some((word) => layerName.toLowerCase().includes(word))) continue;
    for (const nodeId of layer.nodeIds || []) areaById.set(nodeId, layerName);
  }
  const rows = [];
  const seen = new Set();
  for (const node of nodes) {
    const name = String(node.name || "");
    const filePath = node.filePath;
    const inEntryLayer = areaById.has(node.id);
    const pathSignal = Boolean(filePath && PATH_WORDS.test(String(filePath)));
    const isSurfaceClass = node.type === "class" && (inEntryLayer || pathSignal) && SURFACE_WORDS.test(name);
    const isEntryFunction = node.type === "function"
      && ((pathSignal && ENTRY_WORDS.test(name)) || (inEntryLayer && CORE_ENTRY_WORDS.test(name)));
    if (!(isSurfaceClass || isEntryFunction)) continue;
    const key = `${filePath}:${name}`.toLowerCase();
    if (seen.has(key)) continue;
    seen.add(key);
    rows.push(candidate({
      name,
      kind: inferKind(name, filePath),
      signature: name,
      filePath,
      symbol: name,
      area: areaById.get(node.id),
      evidence: { provider: "understand-anything", artifact: target, nodeId: node.id },
    }));
  }
  return rows;
}
function harvestGitnexus(target) {
  const doc = readJson(target);
  const communities = new Map((doc.communities || [])
    .filter((item) => item && typeof item === "object")
    .map((item) => [String(item.id), item.heuristicLabel || item.name]));
  const rows = [];
  for (const route of doc.routes || []) {
    if (!route || typeof route !== "object") continue;
    const signature = String(route.path || route.route || route.name || route.id);
    rows.push(candidate({
      name: String(route.name || signature),
      kind: "http",
      signature,
      filePath: route.filePath,
      symbol: route.symbol,
      area: route.communityLabel,
      evidence: { provider: "gitnexus", artifact: target, nodeId: route.id },
      steps: 1,
    }));
  }
  const grouped = new Map();
  for (const process of doc.processes || []) {
    if (!process || typeof process !== "object") continue;
    const entry = process.entryPointId || process.entry_point_id;
    if (!entry) continue;
    if (!grouped.has(String(entry))) grouped.set(String(entry), []);
    grouped.get(String(entry)).push(process);
  }
  for (const [entryId, processes] of grouped.entries()) {
    const [filePath, symbol] = splitSymbolId(entryId);
    const terminals = [...new Set(processes.map((item) => item.terminalId || item.terminal_id).filter(Boolean).map(String))].sort();
    const communityIds = new Set(processes.flatMap((item) => item.communities || []).map((value) => String(value).replace(/^'|'$/g, "")));
    const labels = [...new Set([...communityIds].filter((value) => communities.get(value)).map((value) => String(communities.get(value))))].sort((a, b) => a.localeCompare(b));
    const cross = processes.some((item) => (item.processType || item.process_type) === "cross_community");
    const name = String(symbol || processes[0].heuristicLabel || entryId);
    rows.push(candidate({
      name,
      kind: inferKind(name, filePath),
      signature: entryId,
      filePath,
      symbol,
      area: labels.join(", ") || processes[0].communityLabel,
      evidence: {
        provider: "gitnexus",
        artifact: target,
        nodeId: entryId,
        processIds: processes.map((item) => item.id).filter(Boolean).map(String).sort(),
        terminalIds: terminals,
      },
      steps: Math.max(...processes.map((item) => Number(item.stepCount || item.steps || 0))),
      boundaries: Math.max(communityIds.size - 1, cross ? 1 : 0),
    }));
  }
  return rows;
}
function uniqueArea(...areas) {
  const labels = [];
  const seen = new Set();
  for (const area of areas) {
    if (!area || area === "Unclassified") continue;
    for (const part of String(area).split(",")) {
      const label = part.trim();
      const key = label.toLowerCase();
      if (label && !seen.has(key)) {
        seen.add(key);
        labels.push(label);
      }
    }
  }
  return labels.sort((a, b) => a.toLowerCase().localeCompare(b.toLowerCase())).join(", ") || "Unclassified";
}
function rowKey(row) {
  const entry = row.entry_ref;
  if (entry.filePath && entry.symbol) return `${entry.filePath}::${entry.symbol}`.toLowerCase();
  return `${entry.kind}::${entry.signature}`.toLowerCase();
}
function nearKey(row) {
  const entry = row.entry_ref;
  const filePath = String(entry.filePath || "").replace(/\\/g, "/").toLowerCase().trim();
  const nameSlug = slugify(row.name);
  if (filePath && nameSlug) return `path+name::${filePath}::${nameSlug}`;
  const signature = String(entry.signature || "").toLowerCase().trim();
  if (signature) return `sig::${signature}`;
  return `exact::${rowKey(row)}`;
}
function foldRow(current, row) {
  for (const item of row.evidence) {
    if (!current.evidence.some((existing) => JSON.stringify(existing) === JSON.stringify(item))) current.evidence.push(item);
  }
  if (row.confidence === "confirmed") {
    current.confidence = "confirmed";
    current.name = row.name;
    current.entry_ref = row.entry_ref;
  }
  current.reach.steps = Math.max(current.reach.steps, row.reach.steps);
  current.reach.boundaries = Math.max(current.reach.boundaries, row.reach.boundaries);
  current.reach.churn = Math.max(current.reach.churn || 0, row.reach.churn || 0);
  current.area = uniqueArea(current.area, row.area);
  if (row.summary && !current.summary) {
    current.summary = row.summary;
    current.written_at = row.written_at;
  }
}
function mergeRows(rows) {
  const merged = new Map();
  for (const row of rows) {
    const key = rowKey(row);
    if (!merged.has(key)) {
      merged.set(key, row);
      continue;
    }
    foldRow(merged.get(key), row);
  }
  const near = new Map();
  for (const row of merged.values()) {
    const key = nearKey(row);
    if (!near.has(key)) {
      near.set(key, row);
      continue;
    }
    foldRow(near.get(key), row);
  }
  return [...near.values()];
}
function writeCommunitiesSummary(repo, exportPath) {
  const doc = readJson(exportPath);
  const byLabel = new Map();
  for (const item of doc.communities || []) {
    if (!item || typeof item !== "object") continue;
    const communityId = String(item.id || "").trim();
    if (!communityId) continue;
    const label = String(item.heuristicLabel || item.name || communityId);
    if (!byLabel.has(label)) byLabel.set(label, []);
    byLabel.get(label).push(communityId);
  }
  ensureTmpDirGitignored(repo);
  const tmp = path.join(path.resolve(repo), TMP_REL);
  const lines = [
    "# Communities (deduplicated by label)", "",
    "Community IDs remain distinct for reach/boundary math; labels are",
    "collapsed here so agent flow analysis is not flooded by duplicates.", "",
    "| Label | Count | Community IDs |",
    "| --- | --- | --- |",
  ];
  const payload = [];
  for (const label of [...byLabel.keys()].sort((a, b) => a.toLowerCase().localeCompare(b.toLowerCase()))) {
    const ids = byLabel.get(label).slice().sort();
    payload.push({ label, count: ids.length, ids });
    let shown = ids.slice(0, 12).join(", ");
    if (ids.length > 12) shown += `, … (+${ids.length - 12})`;
    lines.push(`| ${label.replace(/\|/g, "\\|")} | ${ids.length} | ${shown} |`);
  }
  lines.push("", `_Source: \`${exportPath}\`_`, "");
  const markdownPath = path.join(tmp, "communities.md");
  const jsonPath = path.join(tmp, "communities.json");
  fs.writeFileSync(markdownPath, lines.join("\n"));
  fs.writeFileSync(jsonPath, JSON.stringify({ version: "1.0", labels: payload }, null, 2) + "\n");
  return markdownPath;
}
function score(row) {
  const kindScores = { http: 400, queue: 350, schedule: 300, cli: 280, ui: 250, internal: 80 };
  return (kindScores[row.entry_ref.kind] || 0)
    + (row.confidence === "confirmed" ? 600 : 0)
    + (SURFACE_WORDS.test(row.name) ? 150 : 0)
    + Math.min(row.reach.boundaries, 5) * 80
    + Math.min(row.reach.steps, 20) * 5
    + Math.min(row.reach.churn || 0, 20) * 2
    + Math.min(row.evidence.length, 3) * 20;
}
function addChurn(repo, rows) {
  const result = spawnSync("git", ["-C", repo, "log", "-n", "200", "--name-only", "--pretty=format:"], { encoding: "utf8" });
  if (result.error || result.status !== 0) return;
  const counts = new Map();
  for (const line of result.stdout.split(/\r?\n/)) {
    const relative = line.trim().replace(/\\/g, "/");
    if (relative) counts.set(relative, (counts.get(relative) || 0) + 1);
  }
  for (const row of rows) {
    const filePath = row.entry_ref.filePath;
    row.reach.churn = filePath ? (counts.get(String(filePath).replace(/\\/g, "/")) || 0) : 0;
  }
}
function defaultDocPath(slug, family = null) {
  if (family) return `docs/flows/${family}/${slug}.md`;
  return `docs/flows/${slug}.md`;
}
function applyOrgDefaults(row) {
  const priority = row.priority || rowPriority(row) || "deferred";
  if (!("display_name" in row) || !row.display_name) {
    row.display_name = row.name || row.slug || "unnamed";
  }
  if (!("family" in row)) row.family = null;
  if (!("composed_into" in row)) row.composed_into = null;
  if (!["standalone", "member", "index_only"].includes(row.doc_role)) {
    row.doc_role = priority === "main" ? "standalone" : "index_only";
  }
  if (row.doc_role === "member" || row.doc_role === "index_only") {
    row.doc_path = null;
  } else if (!row.doc_path) {
    row.doc_path = defaultDocPath(row.slug, row.family);
  }
}
function finalize(rows, mainLimit, repo = null) {
  rows = mergeRows(rows);
  if (repo) addChurn(repo, rows);
  for (const row of rows) row.rank = score(row);
  rows.sort((a, b) => b.rank - a.rank || a.name.toLowerCase().localeCompare(b.name.toLowerCase()) || rowKey(a).localeCompare(rowKey(b)));
  const used = new Map();
  rows.forEach((row, index) => {
    const base = baseSlugFor(row);
    used.set(base, (used.get(base) || 0) + 1);
    const slug = used.get(base) === 1 ? base : `${base}-${used.get(base)}`;
    row.slug = slug;
    row.id = `flow-${slug}`;
    const priority = index < Math.max(mainLimit, 0) ? "main" : "deferred";
    row.priority = priority;
    row.status = priority;
    row.display_name = row.name || slug;
    row.family = null;
    row.composed_into = null;
    row.doc_role = priority === "main" ? "standalone" : "index_only";
    row.doc_path = priority === "main" ? defaultDocPath(slug) : null;
  });
  return rows;
}
function loadExistingIndex(repo) {
  const target = path.join(repo, INDEX_REL);
  if (!fs.existsSync(target)) return null;
  try {
    return readJson(target);
  } catch {
    return null;
  }
}
function priorByKey(existing) {
  if (!existing) return new Map();
  return new Map((existing.flows || []).filter((row) => row && typeof row === "object").map((row) => [rowKey(row), row]));
}
function applyReviseStatuses(rows, prior) {
  const orgKeys = ["display_name", "family", "doc_role", "composed_into", "doc_path"];
  const carryKeys = ["summary", "written_at"];
  for (const row of rows) {
    const previous = prior.get(rowKey(row));
    if (!previous) {
      row.status = "placeholder";
      applyOrgDefaults(row);
      continue;
    }
    const priorStatus = previous.status;
    if (priorStatus === "documented" || priorStatus === "skipped") {
      row.status = priorStatus;
      if (previous.slug) {
        row.slug = previous.slug;
        row.id = previous.id || `flow-${previous.slug}`;
      }
      if (previous.priority === "main" || previous.priority === "deferred") row.priority = previous.priority;
    } else {
      row.status = "placeholder";
      if (previous.slug && ["placeholder", "main", "deferred"].includes(previous.status)) {
        row.slug = previous.slug;
        row.id = previous.id || `flow-${previous.slug}`;
      }
    }
    for (const key of orgKeys) {
      if (key in previous && previous[key] != null) {
        row[key] = previous[key];
      } else if (key in previous && ["family", "composed_into", "doc_path"].includes(key)) {
        row[key] = previous[key];
      }
    }
    for (const key of carryKeys) {
      if (key in previous && previous[key] != null) row[key] = previous[key];
    }
    applyOrgDefaults(row);
    if (row.doc_role === "member" || row.doc_role === "index_only") {
      row.doc_path = null;
    } else if (row.priority === "main" && !row.doc_path) {
      row.doc_path = defaultDocPath(row.slug, row.family);
    }
  }
  return rows;
}
function rowPriority(row) {
  if (row.priority === "main" || row.priority === "deferred") return row.priority;
  if (row.status === "main" || row.status === "deferred") return row.status;
  return null;
}
function summaryFor(rows) {
  return {
    total: rows.length,
    main: rows.filter((row) => rowPriority(row) === "main").length,
    deferred: rows.filter((row) => rowPriority(row) === "deferred").length,
    placeholder: rows.filter((row) => row.status === "placeholder").length,
    documented: rows.filter((row) => row.status === "documented").length,
    written: rows.filter((row) => row.status === "documented" && Boolean(row.summary)).length,
    skipped: rows.filter((row) => row.status === "skipped").length,
    confirmed: rows.filter((row) => row.confidence === "confirmed").length,
  };
}
function writeIndex(repo, rows, sources) {
  for (const row of rows) applyOrgDefaults(row);
  const providers = [...new Set(rows.flatMap((row) => row.evidence.map((item) => item.provider)))].sort();
  const value = {
    version: INDEX_VERSION,
    generated_at: nowIso(),
    project: path.basename(path.resolve(repo)),
    sources,
    providers,
    summary: summaryFor(rows),
    flows: rows,
  };
  const target = path.join(repo, INDEX_REL);
  fs.mkdirSync(path.dirname(target), { recursive: true });
  fs.writeFileSync(target, JSON.stringify(value, null, 2) + "\n");
  return target;
}
function resolveDocPath(row) {
  if (row.doc_path) return String(row.doc_path).replace(/\\/g, "/");
  if (row.doc_role === "member" || row.doc_role === "index_only") return null;
  if (row.priority === "main" || row.status === "documented") {
    return defaultDocPath(row.slug, row.family);
  }
  return null;
}
// Stamp the folder sidecar and return the frontmatter-free document text.
function renderDoc(repo, docPath, provenance, title, body) {
  const entry = { id: provenance.doc_id, title, provenance };
  store.writeEntry(repo, docPath, entry);
  return body;
}

function stubBody(row, repo) {
  const name = row.display_name || row.name;
  const docPath = resolveDocPath(row) || defaultDocPath(row.slug, row.family);
  const entry = row.entry_ref;
  const signature = entry.signature || name;
  const provenance = pf.scaffoldProvenance(row.id, docPath, {
    tier: "diligence",
    target_depth: "deep-dive",
    provider: "unknown",
    flow: "derived",
    generated_at: nowIso(),
  });
  const body = [
    `# ${name}`, "",
    "_Last reviewed: {{YYYY-MM-DD}}_", "",
    `Placeholder flow candidate for \`${signature}\`.`, "",
    "Status: `placeholder` — awaiting full flow documentation.", "",
    `- Area: ${row.area || "Unclassified"}`,
    `- Family: ${row.family || "—"}`,
    `- Trigger kind: ${entry.kind}`,
    `- Entry: \`${signature}\``, "",
    "{{Write this document from the evidence required by its catalog entry.}}", "",
  ].join("\n");
  return renderDoc(repo, docPath, provenance, String(name), body);
}
function isScaffoldOrPlaceholder(text) {
  return text.includes("{{") || text.includes("TODO(") || text.includes("Status: `placeholder`") || text.includes("<DOC_ID>");
}
function shouldStub(row) {
  if (row.status !== "placeholder") return false;
  if (row.priority !== "main") return false;
  if (row.doc_role === "member" || row.doc_role === "index_only") return false;
  return true;
}
function ensureStubs(repo, rows) {
  const created = [];
  for (const row of rows) {
    if (!shouldStub(row)) continue;
    const rel = resolveDocPath(row) || defaultDocPath(row.slug, row.family);
    row.doc_path = rel;
    const target = path.join(repo, rel);
    fs.mkdirSync(path.dirname(target), { recursive: true });
    if (fs.existsSync(target)) {
      const existing = fs.readFileSync(target, "utf8");
      if (!isScaffoldOrPlaceholder(existing)) continue;
    }
    fs.writeFileSync(target, stubBody(row, repo));
    created.push({
      id: row.id,
      slug: row.slug,
      path: rel,
      priority: row.priority || "deferred",
      name: row.display_name || row.name,
    });
  }
  return created;
}
function walkMarkdownFiles(dir) {
  const results = [];
  if (!fs.existsSync(dir) || !fs.statSync(dir).isDirectory()) return results;
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) results.push(...walkMarkdownFiles(full));
    else if (entry.isFile() && entry.name.endsWith(".md")) results.push(full);
  }
  return results;
}
function pruneOrphanStubs(repo, rows) {
  const keep = new Set();
  for (const row of rows) {
    if (row.doc_role === "member" || row.doc_role === "index_only") continue;
    if (row.status === "documented" || (row.priority === "main" && row.doc_role === "standalone")) {
      const rel = resolveDocPath(row);
      if (rel) keep.add(rel.replace(/\\/g, "/"));
    }
  }
  const flowsDir = path.join(repo, "docs", "flows");
  if (!fs.existsSync(flowsDir) || !fs.statSync(flowsDir).isDirectory()) return [];
  const removed = [];
  const repoResolved = path.resolve(repo);
  for (const full of walkMarkdownFiles(flowsDir)) {
    const rel = path.relative(repoResolved, full).split(path.sep).join("/");
    if (path.basename(full) === "README.md") continue;
    if (keep.has(rel)) continue;
    let text;
    try {
      text = fs.readFileSync(full, "utf8");
    } catch {
      continue;
    }
    if (!isScaffoldOrPlaceholder(text)) continue;
    fs.unlinkSync(full);
    removed.push(rel);
    const parent = path.dirname(full);
    if (path.resolve(parent) !== path.resolve(flowsDir) && fs.existsSync(parent) && fs.statSync(parent).isDirectory()) {
      if (fs.readdirSync(parent).length === 0) fs.rmdirSync(parent);
    }
  }
  return removed;
}
function flowDocExists(repo, rowOrSlug) {
  if (!repo) return false;
  if (rowOrSlug && typeof rowOrSlug === "object") {
    const rel = resolveDocPath(rowOrSlug);
    if (!rel) return false;
    return fs.existsSync(path.join(repo, rel));
  }
  return fs.existsSync(path.join(repo, "docs", "flows", `${rowOrSlug}.md`));
}
function linkForRow(row) {
  const name = String(row.display_name || row.name).replace(/\|/g, "\\|");
  const rel = resolveDocPath(row);
  if (!rel) return name;
  let link = rel;
  if (link.startsWith("docs/flows/")) link = "./" + link.slice("docs/flows/".length);
  else link = "./" + path.basename(link);
  return `[${name}](${link})`;
}
function markdown(index, tier = "spine", repo = null) {
  const generated = index.generated_at;
  const provider = (index.providers || []).join(", ") || "unknown";
  const provenance = pf.scaffoldProvenance("flows_index", "docs/flows/README.md", {
    tier,
    target_depth: "orientation",
    provider,
    flow: "none",
    generated_at: generated,
  });
  const sections = [];
  if (repo) {
    const flowFile = path.join(repo, ".docforge", "flow-index.json");
    if (fs.existsSync(flowFile) && fs.statSync(flowFile).isFile()) {
      const content = fs.readFileSync(flowFile);
      const blob = crypto.createHash("sha1")
        .update(Buffer.from(`blob ${content.length}\0`))
        .update(content)
        .digest("hex");
      sections.push({
        id: "flow-index",
        sources: [{ path: ".docforge/flow-index.json", git_blob: blob, role: "manifest" }],
        unresolved: [],
      });
    }
  }
  provenance.sections = sections;
  const lines = [
    "# Flows", "",
    "This index lists every evidence-backed flow candidate and routes readers",
    "to the deep-dive flow documents. **Main** priority **standalone** rows get",
    "deep-dive documentation; **member** rows are composed into a parent;",
    "**index_only** / deferred rows stay discoverable without stub files.",
    "",
    "## How to read this index", "",
    "Pick a flow by trigger or entry point. **main** rows are the current",
    "operating paths and own deep-dive documents; **deferred** rows are",
    "evidenced but not yet documented; **placeholder** rows are candidates",
    "awaiting confirmation; **documented** rows point at their flow document;",
      "**skipped** rows were examined and set aside. `Confidence` states how much",
      "evidence backs the candidate; `Reach` is steps / boundaries / changes.",
      "Written deep-dives carry a one-paragraph summary in `Flow summaries`.",
      "",
  ];
  const flows = (index.flows || []).filter((row) => row && typeof row === "object");
  const families = new Map();
  const ungrouped = [];
  for (const row of flows) {
    if (row.family) {
      const key = String(row.family);
      if (!families.has(key)) families.set(key, []);
      families.get(key).push(row);
    } else {
      ungrouped.push(row);
    }
  }
  function appendTable(rows) {
    lines.push("| Status | Role | Flow | Trigger | Entry point | Area | Confidence | Reach |");
    lines.push("|---|---|---|---|---|---|---|---|");
    for (const row of rows) {
      const entry = row.entry_ref;
      let name = row.display_name || row.name;
      if ((row.status === "documented" || row.status === "placeholder") && flowDocExists(repo, row)) {
        name = linkForRow(row);
      } else if (row.status === "documented") {
        name = linkForRow(row);
      } else {
        name = String(name).replace(/\|/g, "\\|");
      }
      if (row.doc_role === "member" && row.composed_into) {
        name = `${name} → \`${row.composed_into}\``;
      }
      const signature = String(entry.signature || "").replace(/\|/g, "\\|");
      const area = String(row.area || "").replace(/\|/g, "\\|");
      const reach = `${row.reach.steps} steps / ${row.reach.boundaries} boundaries / ${row.reach.churn || 0} changes`;
      lines.push(
        `| ${row.status} | ${row.doc_role || "—"} | ${name} | ${entry.kind} | `
        + `\`${signature}\` | ${area} | ${row.confidence} | ${reach} |`,
      );
    }
    lines.push("");
  }
  for (const family of [...families.keys()].sort()) {
    lines.push(`## ${family}`, "");
    appendTable(families.get(family));
  }
  if (ungrouped.length) {
    if (families.size) lines.push("## Ungrouped", "");
    appendTable(ungrouped);
  }
  const documentedWithSummary = flows.filter((row) => row.status === "documented" && row.summary);
  if (documentedWithSummary.length) {
    lines.push("## Flow summaries", "");
    for (const row of documentedWithSummary) {
      const name = String(row.display_name || row.name).replace(/\|/g, "\\|");
      const written = row.written_at || "";
      const suffix = written ? ` — reviewed ${written}` : "";
      lines.push(`### ${name}${suffix}`, "", String(row.summary), "");
    }
  }
  lines.push(`_Generated ${generated}; source of truth: \`.docforge/flow-index.json\`._`, "");
  const body = lines.join("\n");
  return renderDoc(repo, "docs/flows/README.md", provenance, "Flows", body);
}
function findGitnexusInterchange(repo) {
  // The deterministic GitNexus interchange, materialized by the agent from the
  // GitNexus MCP or the offline lbug reader — discovered automatically, never
  // passed as a flag.
  const target = path.join(repo, GITNEXUS_FLOWS_REL);
  if (!fs.existsSync(target) || !fs.statSync(target).isFile()) return null;
  return target;
}
function collectCandidates(args) {
  const rows = [];
  const sources = [];
  let gitnexusInterchange = null;
  const domain = findUa(args.repo, "domain-graph.json");
  const knowledge = findUa(args.repo, "knowledge-graph.json");
  if (domain) {
    rows.push(...harvestUaDomain(domain));
    sources.push(path.relative(args.repo, domain).split(path.sep).join("/"));
  }
  if (knowledge) {
    rows.push(...harvestUaKnowledge(knowledge));
    sources.push(path.relative(args.repo, knowledge).split(path.sep).join("/"));
  }
  gitnexusInterchange = findGitnexusInterchange(args.repo);
  if (gitnexusInterchange) {
    rows.push(...harvestGitnexus(gitnexusInterchange));
    sources.push(path.relative(args.repo, gitnexusInterchange).split(path.sep).join("/"));
  }
  return [rows, sources, gitnexusInterchange];
}
function maybeWriteCommunities(repo, exportPath) {
  if (!exportPath) return null;
  const target = writeCommunitiesSummary(repo, exportPath);
  console.log(`Wrote compact communities summary ${target}.`);
  return target;
}
function parseArgs(argv) {
  if (!argv.length || argv.includes("-h") || argv.includes("--help")) return { help: true };
  const command = argv[0];
  if (!["harvest", "revise", "render", "organize", "update", "import"].includes(command)) {
    throw new Error(`unknown command: ${command}`);
  }
  let index = 1;
  let organizeCommand = null;
  if (command === "organize") {
    if (index >= argv.length || argv[index].startsWith("--")) {
      throw new Error("organize requires a subcommand: emit|apply");
    }
    organizeCommand = argv[index++];
    if (!["emit", "apply"].includes(organizeCommand)) {
      throw new Error(`unknown organize subcommand: ${organizeCommand}`);
    }
  }
  let allowed;
  if (command === "render") allowed = new Set(["repo", "output"]);
  else if (command === "organize" && organizeCommand === "emit") allowed = new Set(["repo", "output"]);
  else if (command === "organize" && organizeCommand === "apply") allowed = new Set(["repo", "organization"]);
  else if (command === "update") allowed = new Set(["repo", "id", "priority", "status", "summary", "written"]);
  else if (command === "import") allowed = new Set(["repo", "analysis", "main-limit"]);
  else allowed = new Set(["repo", "main-limit"]);
  const args = { command, organize_command: organizeCommand, main_limit: 15 };
  for (; index < argv.length; index++) {
    const token = argv[index];
    if (!token.startsWith("--")) throw new Error(`unexpected argument: ${token}`);
    const raw = token.slice(2);
    if (!allowed.has(raw)) throw new Error(`unknown option: ${token}`);
    if (raw === "written") {
      const key = raw.replace(/-/g, "_");
      args[key] = true;
      continue;
    }
    if (index + 1 >= argv.length || argv[index + 1].startsWith("--")) throw new Error(`option requires a value: ${token}`);
    const key = raw.replace(/-/g, "_");
    args[key] = argv[++index];
  }
  if (command === "harvest" || command === "revise" || command === "import") {
    args.main_limit = Number(args.main_limit);
    if (!Number.isInteger(args.main_limit)) throw new Error("--main-limit must be an integer");
  }
  if (command === "update") {
    if (!args.id) throw new Error("--id is required for update");
    if (args.priority && !["main", "deferred"].includes(args.priority)) throw new Error("--priority must be main|deferred");
    if (args.status && !["main", "deferred", "placeholder", "skipped"].includes(args.status)) throw new Error("--status must be main|deferred|placeholder|skipped");
  }
  if (command === "import" && !args.analysis) throw new Error("--analysis is required for import");
  if (command === "organize" && organizeCommand === "apply" && !args.organization) {
    throw new Error("--organization is required for organize apply");
  }
  return args;
}
function usage() {
  console.log([
    "usage: flow_index.js harvest|revise --repo <path> [--main-limit <n>]",
    "       flow_index.js render --repo <path> [--output <path>]",
    "       flow_index.js organize emit --repo <path> [--output <path>]",
    "       flow_index.js organize apply --repo <path> --organization <json>",
    "       flow_index.js update --repo <path> --id <flow-id> [--priority main|deferred] [--status main|deferred|placeholder|skipped] [--summary <text>] [--written]",
    "       flow_index.js import --repo <path> --analysis <flow-analysis.json> [--main-limit <n>]",
  ].join("\n"));
}
function cmdHarvest(args) {
  const [rows, sources, gitnexusInterchange] = collectCandidates(args);
  if (!rows.length) return fail("no flow candidates found; provide UA graphs, a GitNexus .docforge/tmp/gitnexus-flows.json interchange, or use flow_index import --analysis for derived candidates", 2);
  maybeWriteCommunities(args.repo, gitnexusInterchange);
  const finalRows = finalize(rows, args.main_limit, args.repo);
  const target = writeIndex(args.repo, finalRows, sources);
  const summary = summaryFor(finalRows);
  console.log(`Wrote ${target} — ${summary.total} flow candidates (${summary.main} main, ${summary.deferred} deferred).`);
  return 0;
}
function cmdRevise(args) {
  const [rows, sources, gitnexusInterchange] = collectCandidates(args);
  if (!rows.length) return fail("no flow candidates found; provide UA graphs, a GitNexus .docforge/tmp/gitnexus-flows.json interchange, or use flow_index import --analysis for derived candidates", 2);
  const communitiesPath = maybeWriteCommunities(args.repo, gitnexusInterchange);
  let existing = loadExistingIndex(args.repo);
  if (existing) existing = upgradeIndex(existing);
  const prior = priorByKey(existing);
  if (existing && existing.sources) {
    for (const source of existing.sources) {
      if (!sources.includes(source)) sources.push(source);
    }
  }
  let finalRows = finalize(rows, args.main_limit, args.repo);
  finalRows = applyReviseStatuses(finalRows, prior);
  const stubs = ensureStubs(args.repo, finalRows);
  const pruned = pruneOrphanStubs(args.repo, finalRows);
  const target = writeIndex(args.repo, finalRows, sources);
  const summary = summaryFor(finalRows);
  const mainPriority = finalRows
    .filter((row) => row.priority === "main" && row.status !== "skipped" && row.doc_role === "standalone")
    .map((row) => ({
      id: row.id,
      slug: row.slug,
      path: resolveDocPath(row) || defaultDocPath(row.slug, row.family),
      name: row.display_name || row.name,
      status: row.status,
      doc_role: row.doc_role,
    }));
  const documented = finalRows.filter((row) => row.status === "documented").map((row) => row.id);
  console.log(`Revised ${target} — ${summary.total} flows (${summary.placeholder} placeholder, ${summary.documented} documented, ${summary.main} main-priority).`);
  console.log(`Created/refreshed ${stubs.length} main-priority placeholder stub(s).`);
  if (pruned.length) console.log(`Pruned ${pruned.length} orphan scaffold stub(s).`);
  if (mainPriority.length) {
    console.log("NOTICE: main-priority flows eligible for full documentation:");
    for (const item of mainPriority) {
      console.log(`  - ${item.name} (${item.path}) [${item.status}]`);
    }
  }
  console.log(JSON.stringify({
    index: target,
    summary,
    stubs,
    pruned,
    main_priority: mainPriority,
    documented,
    update_existing: documented,
    communities: communitiesPath || null,
  }, null, 2));
  return 0;
}
function buildOrganizationPack(index) {
  const flows = [];
  for (const row of index.flows || []) {
    if (!row || typeof row !== "object") continue;
    const entry = row.entry_ref || {};
    flows.push({
      id: row.id,
      name: row.name,
      display_name: row.display_name || row.name,
      slug: row.slug,
      priority: row.priority,
      status: row.status,
      doc_role: row.doc_role,
      family: row.family,
      composed_into: row.composed_into,
      doc_path: row.doc_path,
      area: row.area,
      rank: row.rank,
      confidence: row.confidence,
      entry_ref: entry,
      module_hint: moduleFromPath(entry.filePath),
    });
  }
  return {
    version: "1.0",
    generated_at: nowIso(),
    project: index.project,
    rules: {
      display_name: "Reader-recognizable business outcome, not a bare symbol.",
      family: "Kebab folder/group key when ≥3 related documentable siblings.",
      compose: "Small related endpoint/service ops sharing a domain become doc_role=member with composed_into pointing at a standalone parent.",
      doc_path: "docs/flows/{family}/{slug}.md when family is set; else docs/flows/{slug}.md.",
      doc_role: {
        standalone: "Own deep-dive markdown (main budget).",
        member: "Section inside parent; no stub file.",
        index_only: "Index row only; typical for deferred.",
      },
    },
    flows,
  };
}
function cmdOrganizeEmit(args) {
  const index = readJson(path.join(args.repo, INDEX_REL));
  for (const row of index.flows || []) {
    if (row && typeof row === "object") applyOrgDefaults(row);
  }
  const pack = buildOrganizationPack(index);
  ensureTmpDirGitignored(args.repo);
  const target = args.output || path.join(args.repo, ORG_PACK_REL);
  fs.mkdirSync(path.dirname(target), { recursive: true });
  fs.writeFileSync(target, JSON.stringify(pack, null, 2) + "\n");
  console.log(`Wrote organization pack ${target} — ${pack.flows.length} flows.`);
  console.log("Next: agent writes .docforge/tmp/flow-organization.json, then flow_index organize apply --organization <path>.");
  return 0;
}
function validateOrganization(org, byId) {
  const errors = [];
  if (org.version !== "1.0") errors.push("organization version must be 1.0");
  const updates = org.updates;
  if (!Array.isArray(updates) || !updates.length) {
    errors.push("organization.updates must be a non-empty array");
    return errors;
  }
  const seenSlugs = new Map();
  for (const row of byId.values()) {
    if (row.doc_role !== "member") seenSlugs.set(row.slug, row.id);
  }
  updates.forEach((update, index) => {
    if (!update || typeof update !== "object" || Array.isArray(update)) {
      errors.push(`updates[${index}] must be an object`);
      return;
    }
    const flowId = update.id;
    if (typeof flowId !== "string" || !byId.has(flowId)) {
      errors.push(`updates[${index}].id must reference an existing flow`);
      return;
    }
    if ("slug" in update && update.slug != null) {
      const slug = update.slug;
      if (typeof slug !== "string" || !SLUG_RE.test(slug)) {
        errors.push(`updates[${index}].slug is invalid`);
      } else {
        const owner = seenSlugs.get(slug);
        if (owner && owner !== flowId) {
          const ownerUpdate = updates.find((u) => u && typeof u === "object" && u.id === owner);
          if (!ownerUpdate || ownerUpdate.slug == null || ownerUpdate.slug === slug) {
            if (!ownerUpdate || !("slug" in ownerUpdate)) {
              errors.push(`updates[${index}].slug '${slug}' already used by ${owner}`);
            }
          }
        }
        seenSlugs.set(slug, flowId);
      }
    }
    if ("family" in update && update.family != null) {
      if (typeof update.family !== "string" || !FAMILY_RE.test(update.family)) {
        errors.push(`updates[${index}].family is invalid`);
      }
    }
    if ("doc_role" in update && update.doc_role != null
      && !["standalone", "member", "index_only"].includes(update.doc_role)) {
      errors.push(`updates[${index}].doc_role is invalid`);
    }
    if ("composed_into" in update && update.composed_into != null) {
      const parent = update.composed_into;
      if (typeof parent !== "string" || !FLOW_ID_RE.test(parent)) {
        errors.push(`updates[${index}].composed_into is invalid`);
      } else if (!byId.has(parent) && parent !== flowId) {
        if (!byId.has(parent)) {
          errors.push(`updates[${index}].composed_into unknown: ${parent}`);
        }
      }
    }
    const members = update.compose_members;
    if (members != null) {
      if (!Array.isArray(members)) {
        errors.push(`updates[${index}].compose_members must be an array`);
      } else {
        for (const memberId of members) {
          if (!byId.has(memberId)) {
            errors.push(`updates[${index}].compose_members unknown id: ${memberId}`);
          }
        }
      }
    }
    if ("doc_path" in update && update.doc_path != null) {
      const docPath = update.doc_path;
      if (typeof docPath !== "string" || !docPath.startsWith("docs/flows/") || !docPath.endsWith(".md")) {
        errors.push(`updates[${index}].doc_path must be under docs/flows/*.md`);
      }
    }
  });
  return errors;
}
function moveOrWriteStub(repo, row, previousPath) {
  const newPath = resolveDocPath(row);
  if (previousPath && previousPath !== newPath) {
    const old = path.join(repo, previousPath);
    if (fs.existsSync(old) && fs.statSync(old).isFile()) {
      const text = fs.readFileSync(old, "utf8");
      if (newPath) {
        const target = path.join(repo, newPath);
        fs.mkdirSync(path.dirname(target), { recursive: true });
        if (!fs.existsSync(target)) {
          fs.writeFileSync(target, text);
        } else if (isScaffoldOrPlaceholder(fs.readFileSync(target, "utf8")) && !isScaffoldOrPlaceholder(text)) {
          fs.writeFileSync(target, text);
        }
      }
      if (isScaffoldOrPlaceholder(text) || (newPath && fs.existsSync(path.join(repo, newPath)))) {
        const newFull = newPath ? path.resolve(path.join(repo, newPath)) : null;
        if (fs.existsSync(old) && (!newPath || path.resolve(old) !== newFull)) {
          fs.unlinkSync(old);
        }
      }
    }
  }
  if (shouldStub(row) && newPath) {
    const target = path.join(repo, newPath);
    fs.mkdirSync(path.dirname(target), { recursive: true });
    if (!fs.existsSync(target) || isScaffoldOrPlaceholder(fs.readFileSync(target, "utf8"))) {
      fs.writeFileSync(target, stubBody(row, repo));
    }
  }
}
function cmdOrganizeApply(args) {
  const index = readJson(path.join(args.repo, INDEX_REL));
  const org = readJson(args.organization);
  const rows = (index.flows || []).filter((row) => row && typeof row === "object");
  for (const row of rows) applyOrgDefaults(row);
  const byId = new Map(rows.map((row) => [row.id, row]));
  const errors = validateOrganization(org, byId);
  if (errors.length) {
    for (const item of errors) process.stderr.write(`error: ${item}\n`);
    return 2;
  }
  const previousPaths = new Map(rows.map((row) => [row.id, resolveDocPath(row)]));
  for (const update of org.updates) {
    const row = byId.get(update.id);
    if ("display_name" in update && update.display_name) row.display_name = String(update.display_name);
    if ("slug" in update && update.slug) row.slug = String(update.slug);
    if ("family" in update) row.family = update.family;
    if ("doc_role" in update && update.doc_role) row.doc_role = update.doc_role;
    if ("composed_into" in update) row.composed_into = update.composed_into;
    if ("doc_path" in update) row.doc_path = update.doc_path;
    const members = update.compose_members || [];
    if (members.length) {
      row.doc_role = "standalone";
      if (row.priority !== "main") row.priority = "main";
      if (!row.doc_path) row.doc_path = defaultDocPath(row.slug, row.family);
      for (const memberId of members) {
        const member = byId.get(memberId);
        member.doc_role = "member";
        member.composed_into = row.id;
        member.family = row.family || member.family;
        member.doc_path = null;
      }
    }
  }
  const usedSlugs = new Map();
  for (const row of rows) {
    applyOrgDefaults(row);
    if (row.doc_role === "member") {
      row.doc_path = null;
      continue;
    }
    if (row.doc_role === "index_only") {
      row.doc_path = null;
      continue;
    }
    if (!row.doc_path) row.doc_path = defaultDocPath(row.slug, row.family);
    const owner = usedSlugs.get(row.slug);
    if (owner && owner !== row.id) return fail(`duplicate slug after apply: ${row.slug}`, 2);
    usedSlugs.set(row.slug, row.id);
  }
  for (const row of rows) {
    moveOrWriteStub(args.repo, row, previousPaths.get(row.id));
  }
  const pruned = pruneOrphanStubs(args.repo, rows);
  index.version = INDEX_VERSION;
  index.generated_at = nowIso();
  index.flows = rows;
  index.summary = summaryFor(rows);
  const target = path.join(args.repo, INDEX_REL);
  fs.writeFileSync(target, JSON.stringify(index, null, 2) + "\n");
  console.log(`Applied organization to ${target} — ${org.updates.length} update(s).`);
  if (pruned.length) console.log(`Pruned ${pruned.length} orphan scaffold stub(s).`);
  console.log(JSON.stringify({
    index: target,
    updates: org.updates.length,
    pruned,
    summary: index.summary,
  }, null, 2));
  return 0;
}
function applyRowUpdate(row, priority, status) {
  // Apply selection fields, then normalize role/path against them.
  if (priority) row.priority = priority;
  if (status) row.status = status;
  if (row.doc_role === "member") {
    row.doc_path = null;
    return;
  }
  if (row.status === "documented") {
    if (row.priority === "main" && !row.doc_path) {
      row.doc_path = defaultDocPath(row.slug, row.family);
    }
    return;
  }
  if (row.status === "skipped" || row.priority === "deferred") {
    row.doc_role = "index_only";
    row.doc_path = null;
    return;
  }
  if (row.priority === "main") {
    row.doc_role = "standalone";
    if (!row.doc_path) row.doc_path = defaultDocPath(row.slug, row.family);
  }
}
function cmdUpdate(args) {
  const index = upgradeIndex(readJson(path.join(args.repo, INDEX_REL)));
  const rows = (index.flows || []).filter((row) => row && typeof row === "object");
  const row = rows.find((item) => item.id === args.id);
  if (!row) return fail(`unknown flow id: ${args.id}`, 2);
  if ((args.summary != null || args.written) && row.status !== "documented") {
    return fail(`flow ${args.id} is not documented; summary write-back requires status 'documented'`, 2);
  }
  applyRowUpdate(row, args.priority || null, args.status || null);
  if (args.summary != null) {
    row.summary = args.summary;
    row.written_at = nowIso();
  } else if (args.written) {
    row.written_at = nowIso();
  }
  index.generated_at = nowIso();
  index.summary = summaryFor(rows);
  const target = path.join(args.repo, INDEX_REL);
  fs.writeFileSync(target, JSON.stringify(index, null, 2) + "\n");
  console.log(`Updated ${target} — ${row.id} [priority=${row.priority}, status=${row.status}, summary=${row.summary ? "yes" : "no"}]`);
  return 0;
}
function analysisRows(analysis, source) {
  // Map derived flow-analysis entries onto flow-index candidate rows.
  const rows = [];
  for (const item of analysis.flows || []) {
    if (!item || typeof item !== "object") continue;
    const name = String(item.name || "").trim();
    if (!name) continue;
    const steps = (item.steps || []).filter((step) => step && typeof step === "object");
    const first = steps[0] || {};
    const filePath = first.path;
    const signature = String(item.entryPoint || name);
    rows.push(candidate({
      name,
      kind: inferKind(name, filePath),
      signature,
      filePath,
      symbol: name,
      area: item.domain,
      evidence: { provider: "codegraph", artifact: source, nodeId: name },
      steps: steps.length,
    }));
  }
  return rows;
}
function cmdImport(args) {
  // Seed derived candidates into the index (CodeGraph-only / no native flow
  // source), merging with existing rows and preserving their state.
  let analysis;
  try {
    analysis = readJson(args.analysis);
  } catch (error) {
    return fail(error.message, 2);
  }
  if (!analysis || typeof analysis !== "object" || !Array.isArray(analysis.flows) || !analysis.flows.length) {
    return fail("analysis must be a JSON object with a non-empty 'flows' list", 2);
  }
  const rows = analysisRows(analysis, String(args.analysis));
  if (!rows.length) return fail("no usable flow rows in the analysis", 2);
  let existing = loadExistingIndex(args.repo);
  if (existing) existing = upgradeIndex(existing);
  const existingRows = existing
    ? (existing.flows || []).filter((row) => row && typeof row === "object")
    : [];
  const sources = existing ? [...(existing.sources || [])] : [];
  const sourceLabel = DERIVED_FLOW_GRAPH_REL.split(path.sep).join("/");
  if (!sources.includes(sourceLabel)) sources.push(sourceLabel);
  const derived = finalize(rows, args.main_limit, args.repo);
  const prior = priorByKey(existing);
  const merged = applyReviseStatuses(derived, prior);
  const mergedKeys = new Set(merged.map((row) => rowKey(row)));
  for (const row of existingRows) {
    if (!mergedKeys.has(rowKey(row))) {
      merged.push(row);
      applyOrgDefaults(row);
    }
  }
  const target = writeIndex(args.repo, merged, sources);
  const summary = summaryFor(merged);
  console.log(`Imported ${rows.length} derived candidate(s) into ${target} — ${summary.total} total rows (${summary.main} main, ${summary.deferred} deferred).`);
  return 0;
}
function cmdRender(args) {
  const index = readJson(path.join(args.repo, INDEX_REL));
  for (const row of index.flows || []) {
    if (row && typeof row === "object") applyOrgDefaults(row);
  }
  let tier = "spine";
  const manifestPath = path.join(args.repo, ".docforge", "manifest.json");
  if (fs.existsSync(manifestPath)) {
    try {
      tier = (((readJson(manifestPath).project || {}).tier) || tier);
    } catch {
      // A malformed manifest is handled by manifest tooling; index render can continue.
    }
  }
  const target = args.output || path.join(args.repo, "docs", "flows", "README.md");
  fs.mkdirSync(path.dirname(target), { recursive: true });
  fs.writeFileSync(target, markdown(index, tier, args.repo));
  console.log(`Rendered ${target} — ${(index.flows || []).length} indexed flows.`);
  return 0;
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
    if (args.command === "harvest") return cmdHarvest(args);
    if (args.command === "revise") return cmdRevise(args);
    if (args.command === "update") return cmdUpdate(args);
    if (args.command === "import") return cmdImport(args);
    if (args.command === "organize") {
      if (args.organize_command === "emit") return cmdOrganizeEmit(args);
      return cmdOrganizeApply(args);
    }
    return cmdRender(args);
  } catch (error) {
    return fail(error.message, 2);
  }
}

process.exit(main());
