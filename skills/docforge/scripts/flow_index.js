#!/usr/bin/env node
"use strict";
/** Harvest, rank, and render Docforge's complete repository flow index. */

const fs = require("fs");
const path = require("path");
const { spawnSync } = require("child_process");
const pf = require("./provenance_frontmatter.js");

const INDEX_REL = path.join(".docforge", "flow-index.json");
const UA_DIRS = [".ua", ".understand-anything"];
const ENTRY_WORDS = /^(?:[Aa]ggregate|[Tt]rack|[Pp]ublish|[Dd]ispatch|[Ee]xecute|[Rr]un|[Ss]tart|[Rr]eceive|[Pp]rocess|[Cc]onsume|[Hh]andle|[Cc]reate|[Uu]pdate|[Dd]elete|[Ss]ave|[Gg]et|[Pp]ost|[Pp]ut|[Pp]atch|[Ss]end)(?:[A-Z0-9_]|$)/;
const CORE_ENTRY_WORDS = /^(?:[Aa]ggregate|[Tt]rack|[Pp]ublish|[Dd]ispatch|[Ee]xecute|[Rr]un|[Ss]tart|[Rr]eceive|[Pp]rocess|[Cc]onsume|[Hh]andle)(?:[A-Z0-9_]|$)/;
const SURFACE_WORDS = /(controller|handler|processor|consumer|listener|worker|job|command|aggregator)$/i;
const PATH_WORDS = /(controllers?|handlers?|processors?|consumers?|workers?|jobs?|commands?|aggregators?|routes?|endpoints?)/i;

function nowIso() {
  return new Date().toISOString().replace(/\.\d{3}Z$/, "+00:00");
}
function fail(message, code = 1) {
  process.stderr.write(`error: ${message}\n`);
  return code;
}
function readJson(target) {
  if (!fs.existsSync(target)) throw new Error(`file not found: ${target}`);
  let value;
  try {
    value = JSON.parse(fs.readFileSync(target, "utf8"));
  } catch (error) {
    throw new Error(`invalid JSON in ${target}: ${error.message}`);
  }
  if (!value || Array.isArray(value) || typeof value !== "object") {
    throw new Error(`expected a JSON object: ${target}`);
  }
  return value;
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
    const labels = [...communityIds].filter((value) => communities.get(value)).map((value) => communities.get(value)).sort();
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
function rowKey(row) {
  const entry = row.entry_ref;
  if (entry.filePath && entry.symbol) return `${entry.filePath}::${entry.symbol}`.toLowerCase();
  return `${entry.kind}::${entry.signature}`.toLowerCase();
}
function mergeRows(rows) {
  const merged = new Map();
  for (const row of rows) {
    const key = rowKey(row);
    if (!merged.has(key)) {
      merged.set(key, row);
      continue;
    }
    const current = merged.get(key);
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
    if (current.area === "Unclassified" && row.area !== "Unclassified") current.area = row.area;
  }
  return [...merged.values()];
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
function finalize(rows, mainLimit, repo = null) {
  rows = mergeRows(rows);
  if (repo) addChurn(repo, rows);
  for (const row of rows) row.rank = score(row);
  rows.sort((a, b) => b.rank - a.rank || a.name.toLowerCase().localeCompare(b.name.toLowerCase()) || rowKey(a).localeCompare(rowKey(b)));
  const used = new Map();
  rows.forEach((row, index) => {
    const base = slugify(row.name);
    used.set(base, (used.get(base) || 0) + 1);
    const slug = used.get(base) === 1 ? base : `${base}-${used.get(base)}`;
    row.slug = slug;
    row.id = `flow-${slug}`;
    const priority = index < Math.max(mainLimit, 0) ? "main" : "deferred";
    row.priority = priority;
    row.status = priority;
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
  for (const row of rows) {
    const previous = prior.get(rowKey(row));
    if (!previous) {
      row.status = "placeholder";
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
    skipped: rows.filter((row) => row.status === "skipped").length,
    confirmed: rows.filter((row) => row.confidence === "confirmed").length,
  };
}
function writeIndex(repo, rows, sources) {
  const providers = [...new Set(rows.flatMap((row) => row.evidence.map((item) => item.provider)))].sort();
  const value = {
    version: "1.0",
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
function stubBody(row) {
  const entry = row.entry_ref;
  const signature = entry.signature || row.name;
  const provenance = pf.scaffoldProvenance(row.id, `docs/flows/${row.slug}.md`, {
    tier: "diligence",
    target_depth: "deep-dive",
    provider: "unknown",
    flow: "derived",
    generated_at: nowIso(),
  });
  return pf.emitYaml(provenance) + [
    `# ${row.name}`, "",
    "_Last reviewed: {{YYYY-MM-DD}}_", "",
    `Placeholder flow candidate for \`${signature}\`.`, "",
    "Status: `placeholder` — awaiting full flow documentation.", "",
    `- Area: ${row.area || "Unclassified"}`,
    `- Trigger kind: ${entry.kind}`,
    `- Entry: \`${signature}\``, "",
    "{{Write this document from the evidence required by its catalog entry.}}", "",
  ].join("\n");
}
function isScaffoldOrPlaceholder(text) {
  return text.includes("{{") || text.includes("TODO(") || text.includes("Status: `placeholder`") || text.includes("<DOC_ID>");
}
function ensureStubs(repo, rows) {
  const created = [];
  const flowsDir = path.join(repo, "docs", "flows");
  fs.mkdirSync(flowsDir, { recursive: true });
  for (const row of rows) {
    if (row.status !== "placeholder") continue;
    const target = path.join(flowsDir, `${row.slug}.md`);
    if (fs.existsSync(target)) {
      const existing = fs.readFileSync(target, "utf8");
      if (!isScaffoldOrPlaceholder(existing)) continue;
    }
    fs.writeFileSync(target, stubBody(row));
    created.push({
      id: row.id,
      slug: row.slug,
      path: `docs/flows/${row.slug}.md`,
      priority: row.priority || "deferred",
      name: row.name,
    });
  }
  return created;
}
function flowDocExists(repo, slug) {
  if (!repo) return false;
  return fs.existsSync(path.join(repo, "docs", "flows", `${slug}.md`));
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
  const lines = [
    "# Flow index", "",
    "This is the complete evidence-backed flow candidate index. `main` priority",
    "rows get deep-dive documentation; `placeholder` rows have stub files;",
    "`deferred` priority rows remain discoverable.", "",
    "| Status | Flow | Trigger | Entry point | Area | Confidence | Reach |",
    "|---|---|---|---|---|---|---|",
  ];
  for (const row of index.flows || []) {
    const entry = row.entry_ref;
    let name = row.name.replace(/\|/g, "\\|");
    if ((row.status === "documented" || row.status === "placeholder") && flowDocExists(repo, row.slug)) {
      name = `[${name}](./${row.slug}.md)`;
    } else if (row.status === "documented") {
      name = `[${name}](./${row.slug}.md)`;
    }
    const signature = String(entry.signature || "").replace(/\|/g, "\\|");
    const area = String(row.area || "").replace(/\|/g, "\\|");
    lines.push(`| ${row.status} | ${name} | ${entry.kind} | \`${signature}\` | ${area} | ${row.confidence} | ${row.reach.steps} steps / ${row.reach.boundaries} boundaries / ${row.reach.churn || 0} changes |`);
  }
  lines.push("", `_Generated ${generated}; source of truth: \`.docforge/flow-index.json\`._`, "");
  return pf.emitYaml(provenance) + lines.join("\n");
}
function collectCandidates(args) {
  const rows = [];
  const sources = [];
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
  if (args.gitnexus_export) {
    rows.push(...harvestGitnexus(args.gitnexus_export));
    sources.push(args.gitnexus_export);
  }
  return [rows, sources];
}
function parseArgs(argv) {
  if (!argv.length || argv.includes("-h") || argv.includes("--help")) return { help: true };
  const command = argv[0];
  if (!["harvest", "revise", "render"].includes(command)) throw new Error(`unknown command: ${command}`);
  const allowed = command === "render" ? new Set(["repo", "output"]) : new Set(["repo", "gitnexus-export", "main-limit"]);
  const args = { command, main_limit: 15 };
  for (let index = 1; index < argv.length; index++) {
    const token = argv[index];
    if (!token.startsWith("--")) throw new Error(`unexpected argument: ${token}`);
    const raw = token.slice(2);
    if (!allowed.has(raw)) throw new Error(`unknown option: ${token}`);
    if (index + 1 >= argv.length || argv[index + 1].startsWith("--")) throw new Error(`option requires a value: ${token}`);
    const key = raw.replace(/-/g, "_");
    args[key] = argv[++index];
  }
  args.main_limit = Number(args.main_limit);
  if (!Number.isInteger(args.main_limit)) throw new Error("--main-limit must be an integer");
  return args;
}
function usage() {
  console.log("usage: flow_index.js harvest|revise --repo <path> [--gitnexus-export <json>] [--main-limit <n>] | render --repo <path> [--output <path>]");
}
function cmdHarvest(args) {
  const [rows, sources] = collectCandidates(args);
  if (!rows.length) return fail("no flow candidates found; provide UA graphs or --gitnexus-export from the GitNexus MCP", 2);
  const finalRows = finalize(rows, args.main_limit, args.repo);
  const target = writeIndex(args.repo, finalRows, sources);
  const summary = summaryFor(finalRows);
  console.log(`Wrote ${target} — ${summary.total} flow candidates (${summary.main} main, ${summary.deferred} deferred).`);
  return 0;
}
function cmdRevise(args) {
  const [rows, sources] = collectCandidates(args);
  if (!rows.length) return fail("no flow candidates found; provide UA graphs or --gitnexus-export from the GitNexus MCP", 2);
  const existing = loadExistingIndex(args.repo);
  const prior = priorByKey(existing);
  if (existing && existing.sources) {
    for (const source of existing.sources) {
      if (!sources.includes(source)) sources.push(source);
    }
  }
  let finalRows = finalize(rows, args.main_limit, args.repo);
  finalRows = applyReviseStatuses(finalRows, prior);
  const stubs = ensureStubs(args.repo, finalRows);
  const target = writeIndex(args.repo, finalRows, sources);
  const summary = summaryFor(finalRows);
  const mainPriority = finalRows
    .filter((row) => row.priority === "main" && row.status !== "skipped")
    .map((row) => ({
      id: row.id,
      slug: row.slug,
      path: `docs/flows/${row.slug}.md`,
      name: row.name,
      status: row.status,
    }));
  const documented = finalRows.filter((row) => row.status === "documented").map((row) => row.id);
  console.log(`Revised ${target} — ${summary.total} flows (${summary.placeholder} placeholder, ${summary.documented} documented, ${summary.main} main-priority).`);
  console.log(`Created/refreshed ${stubs.length} placeholder stub(s).`);
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
    main_priority: mainPriority,
    documented,
    update_existing: documented,
  }, null, 2));
  return 0;
}
function cmdRender(args) {
  const index = readJson(path.join(args.repo, INDEX_REL));
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
    if (!args.repo || !fs.existsSync(args.repo) || !fs.statSync(args.repo).isDirectory()) return fail(`not a directory: ${args.repo || ""}`, 2);
    if (args.command === "harvest") return cmdHarvest(args);
    if (args.command === "revise") return cmdRevise(args);
    return cmdRender(args);
  } catch (error) {
    return fail(error.message, 2);
  }
}

process.exit(main());
