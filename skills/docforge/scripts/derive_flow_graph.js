#!/usr/bin/env node
"use strict";
/* Docforge's own flow-graph derivation — build a provisional domain/flow graph
 * from an existing code graph when no native flow graph is available.
 *
 * Docforge needs a flow graph for docs/flows/, docs/product/, the BA/PO
 * overlays, and agent-context flow sections. When a source supplies one
 * natively (an understand-anything domain graph, or GitNexus's native
 * processes) docforge uses that. When none exists — a code-graph-only source
 * with no flow data — docforge derives one *from the code graph it already
 * has*, grounded in the graph and never invented, and writes it to
 * .docforge/tmp/domain-graph.json: provisional, git-ignored, regenerated each
 * run, never committed.
 *
 * The reasoning step is agent-mediated (a script cannot infer business domains):
 *
 *   node derive_flow_graph.js prepare --repo <path>
 *   # -> writes .docforge/tmp/domain-context.json (compact code-graph digest)
 *   # The agent dispatches the docforge domain analyzer on that context per
 *   # references/domain-derivation.md and saves its JSON to <analysis.json>.
 *   node derive_flow_graph.js write --repo <path> --analysis <analysis.json>
 *   # -> validates and writes .docforge/tmp/domain-graph.json (+ .gitignore)
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
} = require("./graph_storage.js");
const { resolveFirstReady } = require("./graph_source_registry.js");

const TMP_REL = ".docforge/tmp";
const CONTEXT_NAME = "domain-context.json";

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
const FLOW_EDGE_HINTS = ["call", "import", "contain", "handle", "route", "step", "entry"];

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

function buildContext(repo) {
  const [src, graphPath] = resolveFirstReady(repo, "code_graph");
  if (!graphPath) {
    throw new Error(
      "no code graph found — derivation needs one to work from. Run " +
        "precheck_graph.js --need code for how to build it."
    );
  }
  const doc = loadJson(graphPath);
  const nodes = locateCollection(doc, NODE_KEYS);
  const edges = locateCollection(doc, EDGE_KEYS);

  const slimNodes = nodes.map((n) => ({
    id: firstPresent(n, ID_KEYS),
    name: firstPresent(n, LABEL_KEYS),
    type: firstPresent(n, KIND_KEYS),
    path: firstPresent(n, PATH_KEYS),
    summary: firstPresent(n, SUMMARY_KEYS),
  }));
  const slimEdges = [];
  for (const e of edges) {
    const kind = String(firstPresent(e, EDGEKIND_KEYS) || "").toLowerCase();
    if (!FLOW_EDGE_HINTS.some((h) => kind.includes(h))) continue;
    slimEdges.push({
      source: firstPresent(e, SRC_KEYS),
      target: firstPresent(e, DST_KEYS),
      type: firstPresent(e, EDGEKIND_KEYS),
    });
  }

  const layers = Array.isArray(doc.layers) ? doc.layers : [];
  return {
    generatedFrom: graphPath,
    source: src ? src.name : null,
    repo: path.basename(path.resolve(repo)),
    nodeCount: slimNodes.length,
    edgeCount: slimEdges.length,
    nodes: slimNodes,
    edges: slimEdges,
    layers,
  };
}

function runPrepare(args) {
  let context;
  try {
    context = buildContext(args.repo);
  } catch (e) {
    console.error(`PREPARE FAILED: ${e.message}`);
    return 1;
  }
  ensureTmpDirGitignored(args.repo);
  const out = path.join(path.resolve(args.repo), TMP_REL, CONTEXT_NAME);
  fs.mkdirSync(path.dirname(out), { recursive: true });
  fs.writeFileSync(out, JSON.stringify(context, null, 2) + "\n", "utf-8");
  console.log(
    `Wrote ${out} (${context.nodeCount} nodes, ${context.edgeCount} flow-signal edges, ` +
      `source: ${context.source})`
  );
  console.log(
    "Next: dispatch the docforge domain analyzer on this context " +
      "(references/domain-derivation.md), save its JSON, then run:"
  );
  console.log(
    `    node scripts/derive_flow_graph.js write --repo ${args.repo} --analysis <analysis.json>`
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
        "graph (see references/domain-derivation.md)."
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
  const args = { _: [] };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--repo") args.repo = argv[++i];
    else if (a === "--analysis") args.analysis = argv[++i];
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
