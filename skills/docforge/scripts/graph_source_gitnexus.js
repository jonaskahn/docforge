#!/usr/bin/env node
"use strict";
/* GitNexus graph source: index detection, plus building docforge's
 * .ua/knowledge-graph.json and .ua/domain-graph.json from a GitNexus index.
 *
 * GitNexus (https://github.com/abhigyanpatwari/GitNexus) stores its own
 * graph in an opaque embedded database (.gitnexus/lbug) reachable only
 * through MCP tools (`cypher`, resource reads) — there is no file this
 * script can read directly, and no MCP client available to a plain script.
 * So the contract here is agent-mediated: the acting agent runs the three
 * fixed Cypher queries documented in references/gitnexus-bridge.md (fixed
 * RETURN aliases — this script does not guess column names), saves each raw
 * result to a JSON file, then invokes:
 *
 *   node graph_source_gitnexus.js build --repo <path> \
 *       --nodes nodes.json --edges edges.json --processes processes.json
 *
 * detect(repo) only checks whether a GitNexus index exists at all
 * (.gitnexus/meta.json) — it says nothing about whether .ua/*.json has been
 * built from it yet; that's what check_preconditions.js's orchestration is
 * for.
 *
 * Usage:
 *   node graph_source_gitnexus.js detect --repo <path>
 *   node graph_source_gitnexus.js build --repo <path> --nodes <f> --edges <f> --processes <f>
 *
 * Node.js built-ins only.
 */

const fs = require("fs");
const path = require("path");
const { find, writeGraph } = require("./graph_common.js");

const SOURCE_NAME = "gitnexus";

const INDEX_MARKER_CANDIDATES = [".gitnexus/meta.json"];

// Fixed RETURN aliases the bridge doc's Cypher queries must use. Kept as a
// single source of truth so the doc and this script cannot silently drift.
const NODE_COLUMNS = ["id", "name", "path", "type"];
const EDGE_COLUMNS = ["source", "target", "type"];
const PROCESS_COLUMNS = ["processName", "stepIndex", "symbolId", "symbolName", "path"];

function detect(repo) {
  return { index: find(repo, INDEX_MARKER_CANDIDATES) };
}

// Accept either shape a Cypher-query JSON dump might arrive in: a plain
// array of row-objects (most MCP tool results), or a
// {"columns": [...], "rows": [[...], ...]} envelope (common driver output).
// Always returns an array of plain objects keyed by the RETURN aliases.
function normalizeRows(raw) {
  if (Array.isArray(raw)) return raw;
  if (raw && typeof raw === "object" && Array.isArray(raw.rows) && Array.isArray(raw.columns)) {
    return raw.rows.map((row) => Object.fromEntries(raw.columns.map((c, i) => [c, row[i]])));
  }
  throw new Error(
    "unrecognized Cypher result shape — expected a JSON array of row " +
      'objects, or {"columns": [...], "rows": [[...], ...]}'
  );
}

function requireColumns(rows, columns, label) {
  if (!rows.length) return;
  const missing = columns.filter((c) => !(c in rows[0]));
  if (missing.length) {
    throw new Error(
      `${label} rows are missing expected column(s) ${JSON.stringify(missing)} — ` +
        `the Cypher query must RETURN exactly ${JSON.stringify(columns)} ` +
        "(see references/gitnexus-bridge.md)"
    );
  }
}

function buildKnowledgeGraph(nodeRows, edgeRows) {
  requireColumns(nodeRows, NODE_COLUMNS, "node");
  requireColumns(edgeRows, EDGE_COLUMNS, "edge");
  const nodes = nodeRows.map((r) => ({ id: r.id, name: r.name, path: r.path, type: r.type }));
  const edges = edgeRows.map((r) => ({ source: r.source, target: r.target, type: r.type }));
  return { nodes, edges, source: SOURCE_NAME };
}

// Group STEP_IN_PROCESS rows into one flow per process, steps ordered by
// stepIndex. GitNexus's Community clusters are not mapped to domains in this
// first pass — there is no reliable cluster-to-process linkage available
// without a fourth query, so flows are reported flat rather than invented
// under an ungrounded domain grouping.
function buildDomainGraph(processRows) {
  requireColumns(processRows, PROCESS_COLUMNS, "process");
  const flowsByName = new Map();
  for (const r of processRows) {
    if (!flowsByName.has(r.processName)) flowsByName.set(r.processName, []);
    flowsByName.get(r.processName).push(r);
  }

  const flows = [];
  for (const [name, rows] of flowsByName) {
    rows.sort((a, b) => a.stepIndex - b.stepIndex);
    flows.push({
      name,
      steps: rows.map((r) => ({
        order: r.stepIndex,
        symbolId: r.symbolId,
        symbolName: r.symbolName,
        path: r.path,
      })),
    });
  }
  return { flows, source: SOURCE_NAME };
}

function loadJson(p) {
  let text;
  try {
    text = fs.readFileSync(p, "utf-8");
  } catch {
    throw new Error(`file not found: ${p}`);
  }
  try {
    return JSON.parse(text);
  } catch (e) {
    throw new Error(`invalid JSON in ${p}: ${e.message}`);
  }
}

function parseArgs(argv) {
  const args = { _: [] };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--repo") args.repo = argv[++i];
    else if (a === "--nodes") args.nodes = argv[++i];
    else if (a === "--edges") args.edges = argv[++i];
    else if (a === "--processes") args.processes = argv[++i];
    else args._.push(a);
  }
  return args;
}

function cmdDetect(args) {
  const result = detect(args.repo);
  if (result.index) {
    console.log(`READY  gitnexus index  -> ${result.index}`);
    return 0;
  }
  console.log("MISSING  gitnexus index  (checked for .gitnexus/meta.json)");
  console.log("  Fix: from the repo root, run:");
  console.log("    npx gitnexus analyze");
  console.log("    npx gitnexus setup");
  console.log("  Then re-run this check.");
  return 1;
}

function cmdBuild(args) {
  try {
    const nodeRows = normalizeRows(loadJson(args.nodes));
    const edgeRows = normalizeRows(loadJson(args.edges));
    const processRows = normalizeRows(loadJson(args.processes));
    const knowledgeGraph = buildKnowledgeGraph(nodeRows, edgeRows);
    const domainGraph = buildDomainGraph(processRows);
    const [kgPath, dgPath] = writeGraph(args.repo, knowledgeGraph, domainGraph);
    console.log(
      `Wrote ${kgPath} (${knowledgeGraph.nodes.length} nodes, ${knowledgeGraph.edges.length} edges)`
    );
    console.log(`Wrote ${dgPath} (${domainGraph.flows.length} flows)`);
    console.log("Re-run check_preconditions.js --need domain to confirm READY.");
    return 0;
  } catch (e) {
    console.error(`BUILD FAILED: ${e.message}`);
    return 1;
  }
}

function main() {
  const argv = process.argv.slice(2);
  const command = argv[0];
  const args = parseArgs(argv.slice(1));

  if (command !== "detect" && command !== "build") {
    console.error("usage: graph_source_gitnexus.js <detect|build> --repo <path> [...]");
    return 2;
  }
  if (!args.repo) {
    console.error("--repo is required");
    return 2;
  }
  if (!fs.existsSync(args.repo) || !fs.statSync(args.repo).isDirectory()) {
    console.error(`Not a directory: ${args.repo}`);
    return 2;
  }

  if (command === "detect") return cmdDetect(args);

  if (!args.nodes || !args.edges || !args.processes) {
    console.error("build requires --nodes, --edges, and --processes");
    return 2;
  }
  return cmdBuild(args);
}

module.exports = {
  SOURCE_NAME,
  INDEX_MARKER_CANDIDATES,
  NODE_COLUMNS,
  EDGE_COLUMNS,
  PROCESS_COLUMNS,
  detect,
  normalizeRows,
  buildKnowledgeGraph,
  buildDomainGraph,
};

if (require.main === module) {
  process.exit(main());
}
