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
} = require("../../graph/js/graph_storage.js");
const {
  readGraphLock,
  resolveAllReady,
  resolveLocked,
} = require("../../graph/js/graph_source_registry.js");
const { maxFlowsFor } = require("./budgets.js");

const TMP_REL = ".docforge/tmp";
const CONTEXT_NAME = "flow-context.json";

// Main-flow budget and traversal radius for the entry-point-first strategy.
const DEFAULT_MAX_FLOWS = 15;
// A real request path is route -> controller -> service -> model -> client.
// Three hops truncated most flows mid-way; six reaches the terminal on the
// repos this was measured against.
const DEFAULT_HOPS = 6;

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
// `reference` earns its place: in a route-based codebase the route reaches its
// handler through a `references` edge, so omitting it broke every request chain
// at hop zero. `instantiate` and `dispatch` cover the same gap in OO and event
// codebases.
const FLOW_EDGE_HINTS = ["call", "import", "handle", "route", "step", "entry",
  "reference", "instantiate", "dispatch"];

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

// How the provider was chosen, for the context file and the report. Sharing one
// vocabulary between resolveLocked, the JSON, and stdout keeps them from drifting.
const ORIGIN_LABELS = {
  lock: "session lock",
  priority: "registry priority, no lock recorded",
};

/** Record how the provider was chosen, right beside which one it was. A lock is
 * only trustworthy if a run can be seen to have honored it. */
function withOrigin(context, origin) {
  context.sourceOrigin = origin;
  return context;
}

/** A locked provider whose graph has left the disk. Hard-fail rather than quietly
 * deriving from a provider the user declined: the provider decides the readMode
 * and the entry-point seeds, so falling back would silently change the shape of
 * the analysis mid-session, and every document already written carries the locked
 * provider in its provenance. */
function staleLockMessage(repo, provider) {
  const lines = [
    `graph provider '${provider}' is locked for this session in ` +
      ".docforge/manifest.json, but its graph is not on disk (moved, deleted, " +
      "or never built).",
  ];
  const ready = resolveAllReady(repo, "code_graph").map(([src]) => src.name);
  if (ready.length) {
    lines.push(`Ready now: ${ready.join(", ")}.`);
    lines.push(
      "Rebuild the locked graph, or relock deliberately: " +
        `manage_manifest.py set-graph --repo <repo> --provider ${ready[0]} --force`
    );
  } else {
    lines.push(
      "No provider is ready — run precheck_graph.py --need code for how to " +
        "build one, then relock with set-graph --force if you change provider."
    );
  }
  return lines.join(" ");
}

/* Resolve the code graph and build the analyzer context, dispatched on the
 * source's read_mode. Only a JSON source is ever text-loaded here — a db/mcp
 * source is routed to its native interface, so a binary graph never reaches a
 * JSON reader (the crash fix).
 *
 * The provider comes from the session lock, not registry priority: the user
 * already answered which graph to use and `init` recorded it, so re-detecting
 * here would analyze a provider they declined (references/graph/graph-sources.md
 * "Session persistence"). */
function buildContext(repo, maxFlows, hops) {
  const [src, graphPath, origin] = resolveLocked(repo, "code_graph");
  if (origin === "lock-stale") {
    const lock = readGraphLock(repo);
    throw new Error(staleLockMessage(repo, lock ? String(lock.provider) : "unknown"));
  }
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
      return withOrigin(
        entryPointContext(doc, seeds, src, graphPath, repo, maxFlows, hops),
        origin
      );
    }
    return withOrigin(flatContext(doc, src, graphPath, repo), origin);
  }

  // db / mcp: binary graph — never loadJson it.
  const seeds = entryFn ? entryFn(repo) : [];
  if (seeds.length) {
    // An offline seed reader is available for this DB source. Where that reader
    // can also walk ordered chains, ship the chains: handing the analyzer a
    // bare seed list is what left it inventing step order.
    const main = seeds.slice(0, maxFlows);
    const clusters = readerClusters(src, repo, main, hops);
    const context = {
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
    };
    if (clusters.length) {
      context.clusters = clusters;
      context.note =
        "Each cluster's `paths` are ordered call chains read from the source, " +
        "every hop carrying file and line — use them as the step skeleton. " +
        "Confirm actors, branches, rules, and failures against source (or " +
        "codegraph_explore) before writing; the graph gives structure, not " +
        "business meaning.";
    } else {
      context.note =
        "Seeds read offline; spread each via the source's reader or MCP, main " +
        "flows first (references/graph/flow-derivation.md).";
    }
    return withOrigin(context, origin);
  }
  return withOrigin(nativeInterfaceContext(src, graphPath, repo, readMode), origin);
}

/** Ordered call chains per seed, when the source exposes a path reader.
 *
 * Only CodeGraph supplies one today. A source without it still gets a seed
 * list, which is what it had before — this never fails the prepare step. */
function readerClusters(src, repo, seeds, hops) {
  if (!src || src.name !== "codegraph") return [];
  let orderedPaths;
  try {
    ({ orderedPaths } = require("../../graph/js/graph_source_codegraph_reader.js"));
  } catch {
    return [];
  }
  return seeds.map((seed) => ({
    entryPoint: { id: seed.id, name: seed.name, kind: seed.kind, path: seed.path, line: seed.line },
    rank: seed.rank,
    paths: orderedPaths(repo, seed.id, hops),
  }));
}

/** `<name> [<how it was chosen>]` — one helper so the three strategy branches and
 * both runtimes cannot drift on the wording. */
function sourceLabel(context) {
  const label = ORIGIN_LABELS[context.sourceOrigin];
  return label ? `${context.source} [${label}]` : String(context.source);
}

function reportPrepare(context) {
  const strategy = context.strategy;
  if (strategy === "entry-point-first") {
    console.log(
      `Strategy: entry-point-first — ${context.mainFlows} main flow(s) of ` +
        `${context.entryPointCount} entry points (${context.tail} in the tail), ` +
        `source: ${sourceLabel(context)}`
    );
  } else if (strategy === "flat-fallback") {
    console.log(
      `Strategy: flat-fallback (no entry-point signal) — ${context.nodeCount} ` +
        `nodes, ${context.edgeCount} flow-signal edges, source: ${sourceLabel(context)}`
    );
  } else {
    console.log(
      `Strategy: ${strategy} — read via the source's native interface, source: ` +
        `${sourceLabel(context)} (no graph dumped)`
    );
  }
  if (context.sourceOrigin === "priority") {
    // The self-heal path graph-sources.md documents: a manifest written before
    // the lock existed, or a run before init.
    console.log(
      'Note: no provider is locked in manifest["graph"]; this pick is registry ' +
        "priority. Pin it with `manage_manifest.py set-graph --repo <repo>`."
    );
  }
}

function runPrepare(args) {
  let context;
  try {
    context = buildContext(args.repo, maxFlowsFor(args.repo, args.maxFlows), args.hops);
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
  let contextOrigin = null;
  const ctxFile = path.join(path.resolve(args.repo), TMP_REL, CONTEXT_NAME);
  if (fs.existsSync(ctxFile)) {
    try {
      const ctx = JSON.parse(fs.readFileSync(ctxFile, "utf-8"));
      contextSrc = ctx.source;
      contextPath = ctx.generatedFrom;
      contextOrigin = ctx.sourceOrigin;
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
  // Free provenance on a provisional artifact whose whole risk is "which provider
  // did this actually come from".
  if (contextOrigin) flowGraph.sourceOrigin = contextOrigin;
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
  // maxFlows: null — the scale-aware default (budgets.js) applies unless an
  // explicit value was passed; DEFAULT_MAX_FLOWS documents the fallback.
  const args = { _: [], maxFlows: null, hops: DEFAULT_HOPS };
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
