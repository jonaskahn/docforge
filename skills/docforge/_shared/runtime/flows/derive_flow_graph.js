#!/usr/bin/env node
"use strict";
/* Docforge's own flow-graph derivation — build a provisional flow graph
 * from an existing code graph when no native flow graph is available.
 *
 * Docforge needs a flow graph only for selected manifest documents that
 * declare the `flow_graph` capability. When a source supplies one
 * natively (an understand-anything flow graph, or GitNexus's native
 * processes) docforge uses that. When none exists — a code-graph-only source
 * with no flow data — docforge derives one *from the code graph it already
 * has*, grounded in the graph and never invented, and writes it to
 * .docforge/tmp/flow-graph.json: provisional, git-ignored, regenerated each
 * run, never committed.
 *
 * The reasoning step is agent-mediated (a script cannot infer business domains).
 * After flow_index harvest|revise, prefer the compact pack: main-priority rows
 * from .docforge/flow-index.json, .docforge/tmp/communities.md (deduped
 * labels), and this prepare context when no native flow graph exists:
 *
 *   node derive_flow_graph.js prepare --repo <path>
 *   # -> writes .docforge/tmp/flow-context.json (compact code-graph digest)
 *   # The agent analyzes main-priority flows per references/graph/flow-derivation.md
 *   # into .docforge/tmp/flow-analysis.json (or another --analysis path).
 *   node derive_flow_graph.js write --repo <path> --analysis <analysis.json>
 *   # -> validates and writes .docforge/tmp/flow-graph.json (+ .gitignore)
 *
 * Docforge's flow shape:
 *   { "derived": true, "source": "<code-graph source>",
 *     "generatedFrom": "<code-graph path>", "generatedAt": "<iso>",
 *     "flows": [ { "name", "domain"?, "entryPoint"?,
 *                  "steps": [ { "order", "name", "path"? } ] } ] }
 *
 * Node.js built-ins only.
 */

const fs = require("fs");
const path = require("path");
const {
  ensureTmpDirGitignored,
  validateFlowGraphShape,
  writeFlowGraph,
} = require("../graph/graph_storage.js");
const { resolveFirstReady } = require("../graph/graph_source_registry.js");

const TMP_REL = ".docforge/tmp";
const CONTEXT_NAME = "flow-context.json";

// Main-flow budget and traversal radius for the entry-point-first strategy.
const DEFAULT_MAX_FLOWS = 15;
const DEFAULT_HOPS = 3;

// Loose key probing — the code-graph schema varies by source, so search rather
// than assume (mirrors read_graph.js's tolerance).
const NODE_KEYS = ["nodes", "files", "entities", "items"];
const EDGE_KEYS = ["edges", "links", "relationships", "relations"];
const ID_KEYS = ["id", "nodeId", "key", "name"];
const PATH_KEYS = ["path", "filePath", "file", "relativePath", "location"];
const LABEL_KEYS = ["name", "label", "title", "symbol"];
const KIND_KEYS = ["type", "kind", "nodeType", "category"];
const SUMMARY_KEYS = ["summary", "description", "explanation", "doc"];
const SRC_KEYS = ["source", "from", "src", "start"];
const DST_KEYS = ["target", "to", "dst", "end"];
const EDGEKIND_KEYS = ["type", "kind", "relation", "label"];
const FLOW_EDGE_HINTS = ["call", "import", "handle", "route", "step", "entry"];

function firstPresent(d, keys) {
  for (const k of keys) {
    if (d && typeof d === "object" && k in d && d[k] !== null && d[k] !== "") {
      return d[k];
    }
  }
  return null;
}

function locateCollection(doc, keys, depth = 3) {
  if (!doc || typeof doc !== "object" || Array.isArray(doc) || depth < 0) return [];
  for (const k of keys) {
    const v = doc[k];
    if (Array.isArray(v) && (v.length === 0 || (typeof v[0] === "object" && v[0] !== null))) {
      return v;
    }
    if (v && typeof v === "object" && !Array.isArray(v)) {
      const vals = Object.values(v);
      if (vals.length && typeof vals[0] === "object" && vals[0] !== null) return vals;
    }
  }
  for (const v of Object.values(doc)) {
    if (v && typeof v === "object" && !Array.isArray(v)) {
      const found = locateCollection(v, keys, depth - 1);
      if (found.length) return found;
    }
  }
  return [];
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

// Normalize source nodes to docforge's slim shape and index them by id.
function slimNodesOf(nodes) {
  const slim = [];
  const byId = new Map();
  for (const n of nodes) {
    const id = firstPresent(n, ID_KEYS);
    const record = {
      id,
      name: firstPresent(n, LABEL_KEYS),
      type: firstPresent(n, KIND_KEYS),
      path: firstPresent(n, PATH_KEYS),
      summary: firstPresent(n, SUMMARY_KEYS),
    };
    slim.push(record);
    if (id != null) byId.set(String(id), record);
  }
  return { slim, byId };
}

// Keep only edges that carry flow/structure signal, in slim shape.
function flowEdgesOf(edges) {
  const slim = [];
  for (const e of edges) {
    const kind = String(firstPresent(e, EDGEKIND_KEYS) || "").toLowerCase();
    if (!FLOW_EDGE_HINTS.some((h) => kind.includes(h))) continue;
    slim.push({
      source: firstPresent(e, SRC_KEYS),
      target: firstPresent(e, DST_KEYS),
      type: firstPresent(e, EDGEKIND_KEYS),
    });
  }
  return slim;
}

// Breadth-first walk from a seed over flow edges, collecting node ids reachable
// within `hops` hops (the seed's flow neighbourhood).
function boundedCluster(seedId, adjacency, byId, hops) {
  const seen = new Set([String(seedId)]);
  let frontier = [String(seedId)];
  for (let h = 0; h < Math.max(hops, 0); h++) {
    const next = [];
    for (const nid of frontier) {
      for (const target of adjacency.get(nid) || []) {
        if (!seen.has(target)) {
          seen.add(target);
          next.push(target);
        }
      }
    }
    frontier = next;
    if (frontier.length === 0) break;
  }
  const out = [];
  for (const nid of seen) if (byId.has(nid)) out.push(byId.get(nid));
  return out;
}

// Entry-point-first context: the top `maxFlows` seeds, each with its bounded
// flow neighbourhood — dozens of nodes per flow, not the whole graph.
function entryPointContext(doc, seeds, src, graphPath, repo, maxFlows, hops) {
  const { slim, byId } = slimNodesOf(locateCollection(doc, NODE_KEYS));
  const edges = flowEdgesOf(locateCollection(doc, EDGE_KEYS));
  const adjacency = new Map();
  for (const e of edges) {
    if (e.source != null && e.target != null) {
      const key = String(e.source);
      if (!adjacency.has(key)) adjacency.set(key, []);
      adjacency.get(key).push(String(e.target));
    }
  }

  const main = seeds.slice(0, maxFlows);
  const clusters = [];
  for (const seed of main) {
    const clusterNodes = boundedCluster(seed.id, adjacency, byId, hops);
    const clusterIds = new Set(clusterNodes.map((n) => String(n.id)));
    const clusterEdges = edges.filter(
      (e) => clusterIds.has(String(e.source)) && clusterIds.has(String(e.target))
    );
    clusters.push({
      entryPoint: { id: seed.id, name: seed.name, kind: seed.kind, path: seed.path },
      rank: seed.rank,
      nodes: clusterNodes,
      edges: clusterEdges,
    });
  }
  return {
    strategy: "entry-point-first",
    generatedFrom: graphPath,
    source: src ? src.name : null,
    repo: path.basename(path.resolve(repo)),
    maxFlows,
    hops,
    entryPointCount: seeds.length,
    mainFlows: main.length,
    tail: Math.max(seeds.length - main.length, 0),
    clusters,
  };
}

// Fallback: the whole flow-signal graph in one dump (pre-entry-point
// behaviour), used only when no entry-point signal is available.
function flatContext(doc, src, graphPath, repo) {
  const { slim } = slimNodesOf(locateCollection(doc, NODE_KEYS));
  const edges = flowEdgesOf(locateCollection(doc, EDGE_KEYS));
  const layers = Array.isArray(doc.layers) ? doc.layers : [];
  return {
    strategy: "flat-fallback",
    generatedFrom: graphPath,
    source: src ? src.name : null,
    repo: path.basename(path.resolve(repo)),
    nodeCount: slim.length,
    edgeCount: edges.length,
    nodes: slim,
    edges,
    layers,
  };
}

// A DB/MCP source whose graph is not a JSON file docforge can load. It is never
// text-loaded here (that is the crash fix) — instead the agent reads it through
// the source's native interface.
function nativeInterfaceContext(src, graphPath, repo, readMode) {
  const instruction =
    "This source's graph is not a JSON file docforge parses; do NOT dump the " +
    "whole graph. Resolve flows entry-point-first through the source's native " +
    "interface (references/graph/flow-derivation.md): " +
    (readMode === "mcp"
      ? "for CodeGraph, use the codegraph MCP to rank entry points (route nodes, " +
        "then exported functions with no incoming call, then call fan-out) and " +
        "run codegraph_explore once per main entry point, documenting the top " +
        "flows first."
      : "read the source's native flows/processes directly and rank them " +
        "main-first (e.g. GitNexus: cross_community processes, then step count); " +
        "do not derive what the source already models.");
  return {
    strategy: readMode === "mcp" ? "mcp-explore" : "native-interface",
    generatedFrom: graphPath,
    source: src ? src.name : null,
    repo: path.basename(path.resolve(repo)),
    readMode,
    instruction,
  };
}

// Resolve the code graph and build the analyzer context, dispatched on the
// source's read_mode. Only a JSON source is ever text-loaded here — a db/mcp
// source is routed to its native interface, so a binary graph never reaches a
// JSON reader (the crash fix).
function buildContext(repo, maxFlows, hops) {
  const [src, graphPath] = resolveFirstReady(repo, "code_graph");
  if (!graphPath) {
    throw new Error(
      "no code graph found — derivation needs one to work from. Run " +
        "precheck_graph.js --need code for how to build it."
    );
  }
  const readMode = src ? src.readMode : "json";
  const entryFn = src ? src.entryPoints : null;

  if (readMode === "json") {
    const doc = loadJson(graphPath);
    const seeds = entryFn ? entryFn(repo) : [];
    if (seeds.length) {
      return entryPointContext(doc, seeds, src, graphPath, repo, maxFlows, hops);
    }
    return flatContext(doc, src, graphPath, repo);
  }

  // db / mcp: binary graph — never loadJson it.
  const seeds = entryFn ? entryFn(repo) : [];
  if (seeds.length) {
    const main = seeds.slice(0, maxFlows);
    return {
      strategy: "entry-point-first",
      generatedFrom: graphPath,
      source: src ? src.name : null,
      repo: path.basename(path.resolve(repo)),
      maxFlows,
      hops,
      entryPointCount: seeds.length,
      mainFlows: main.length,
      tail: Math.max(seeds.length - main.length, 0),
      entryPoints: main,
      note:
        "Seeds read offline; spread each via the source's reader or MCP, main " +
        "flows first (references/graph/flow-derivation.md).",
    };
  }
  return nativeInterfaceContext(src, graphPath, repo, readMode);
}

function reportPrepare(context) {
  const strategy = context.strategy;
  if (strategy === "entry-point-first") {
    console.log(
      `Strategy: entry-point-first — ${context.mainFlows} main flow(s) of ` +
        `${context.entryPointCount} entry points (${context.tail} in the tail), ` +
        `source: ${context.source}`
    );
  } else if (strategy === "flat-fallback") {
    console.log(
      `Strategy: flat-fallback (no entry-point signal) — ${context.nodeCount} ` +
        `nodes, ${context.edgeCount} flow-signal edges, source: ${context.source}`
    );
  } else {
    console.log(
      `Strategy: ${strategy} — read via the source's native interface, source: ` +
        `${context.source} (no graph dumped)`
    );
  }
}

function runPrepare(args) {
  let context;
  try {
    context = buildContext(args.repo, args.maxFlows, args.hops);
  } catch (e) {
    console.error(`PREPARE FAILED: ${e.message}`);
    return 1;
  }
  ensureTmpDirGitignored(args.repo);
  const out = path.join(path.resolve(args.repo), TMP_REL, CONTEXT_NAME);
  fs.mkdirSync(path.dirname(out), { recursive: true });
  fs.writeFileSync(out, JSON.stringify(context, null, 2) + "\n", "utf-8");
  console.log(`Wrote ${out}`);
  reportPrepare(context);
  console.log(
    "Next: dispatch the Docforge flow analyzer on this context, main flows " +
      "first (references/graph/flow-derivation.md), save its JSON, then run:"
  );
  console.log(
    `    node runtime/cli/js/derive_flow_graph.js write --repo ${args.repo} --analysis <analysis.json>`
  );
  return 0;
}

function runWrite(args) {
  let analysis;
  try {
    analysis = loadJson(args.analysis);
  } catch (e) {
    console.error(`WRITE FAILED: ${e.message}`);
    return 1;
  }
  if (typeof analysis !== "object" || analysis === null || Array.isArray(analysis)) {
    console.error("WRITE FAILED: analysis must be a JSON object with a 'flows' list");
    return 1;
  }

  let contextSrc = null;
  let contextPath = null;
  const ctxFile = path.join(path.resolve(args.repo), TMP_REL, CONTEXT_NAME);
  if (fs.existsSync(ctxFile)) {
    try {
      const ctx = JSON.parse(fs.readFileSync(ctxFile, "utf-8"));
      contextSrc = ctx.source;
      contextPath = ctx.generatedFrom;
    } catch {
      /* ignore */
    }
  }

  const flowGraph = {
    derived: true,
    source: analysis.source || contextSrc,
    generatedFrom: analysis.generatedFrom || contextPath,
    generatedAt: new Date().toISOString(),
    flows: analysis.flows,
  };
  if ("domains" in analysis) flowGraph.domains = analysis.domains;

  const error = validateFlowGraphShape(flowGraph);
  if (error) {
    console.error(
      `WRITE FAILED: ${error}. The analyzer must return a non-empty 'flows' ` +
        "list — if the code graph evidences no flows, do not write an empty " +
        "graph (see references/graph/flow-derivation.md)."
    );
    return 1;
  }

  ensureTmpDirGitignored(args.repo);
  const p = writeFlowGraph(args.repo, flowGraph, TMP_REL);
  console.log(`Wrote ${p} (${flowGraph.flows.length} flows, provisional/derived — never committed)`);
  console.log("Re-run precheck_graph.js --need flow to confirm READY.");
  return 0;
}

function parseArgs(argv) {
  const args = { _: [], maxFlows: DEFAULT_MAX_FLOWS, hops: DEFAULT_HOPS };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--repo") args.repo = argv[++i];
    else if (a === "--analysis") args.analysis = argv[++i];
    else if (a === "--max-flows") args.maxFlows = parseInt(argv[++i], 10);
    else if (a === "--hops") args.hops = parseInt(argv[++i], 10);
    else args._.push(a);
  }
  return args;
}

function main() {
  const argv = process.argv.slice(2);
  const command = argv[0];
  const args = parseArgs(argv.slice(1));

  if (command !== "prepare" && command !== "write") {
    console.error("usage: derive_flow_graph.js <prepare|write> --repo <path> [--analysis <f>]");
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

  if (command === "prepare") return runPrepare(args);
  if (!args.analysis) {
    console.error("write requires --analysis <analysis.json>");
    return 2;
  }
  return runWrite(args);
}

process.exit(main());
