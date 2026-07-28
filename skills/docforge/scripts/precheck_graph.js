#!/usr/bin/env node
"use strict";
/* Gate docforge documentation work on the graph analysis it depends on —
 * provider-agnostic, over whatever graph sources are registered in
 * graph_source_registry.js (understand-anything, GitNexus, and any future source).
 *
 * Two capabilities matter:
 *
 *   code_graph  — structure and call/import relationships. Universal precondition.
 *                 Docforge does nothing without one, but *any* single
 *                 registered source that has built one satisfies it; docforge
 *                 never fabricates a code graph itself.
 *
 *   flow_graph  — business flows and ordered steps. Needed only when a selected
 *                 catalog entry declares it. Resolved native-first (a
 *                 source that emits flows), else docforge derives a provisional
 *                 one from the code graph into .docforge/tmp/flow-graph.json
 *                 (never committed — see derive_flow_graph.js). So flow docs
 *                 are never hard-blocked while a code graph exists.
 *
 * This script only inspects the filesystem; the agent confirms whether a
 * producer plugin/skill is installed using the setup hints printed here.
 *
 * When more than one source is ready for the same repo, this reports all of
 * them (with each one's read mechanism) so the agent can choose by the
 * provider fit documented in references/graph-sources.md.
 *
 * Exit code 0 when the requested --need scope is satisfiable; non-zero
 * otherwise, with per-source remediation.
 *
 * Usage:
 *   node precheck_graph.js --repo <path>              # --need code (default)
 *   node precheck_graph.js --repo <path> --need flow
 *
 * Node.js built-ins only.
 */

const fs = require("fs");
const { relativeDisplayPath, findGraphFile, listKnownGraphDirs } = require("./graph_storage.js");
const { setupHintsForMissing, resolveAllReady } = require("./graph_source_registry.js");

const DERIVED_FLOW_CANDIDATES = [".docforge/tmp/flow-graph.json"];

// How each source's graph is read, keyed by its readMode, for the report.
const READ_MECHANISM = {
  json: "JSON on disk — read with read_graph.js",
  db:
    "ladybug DB — query via the gitnexus MCP, or offline with " +
    "graph_source_gitnexus_reader.js",
  mcp:
    "SQLite index — query via the codegraph MCP tool (codegraph_explore); " +
    "no offline reader — confirm it is wired to this session first, else " +
    "`codegraph install`",
};

function parseArgs(argv) {
  const args = { need: "code" };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--repo" || a === "--need") {
      if (i + 1 >= argv.length || argv[i + 1].startsWith("--")) {
        throw new Error(`option requires a value: ${a}`);
      }
      args[a.slice(2)] = argv[++i];
    }
    else if (a === "-h" || a === "--help") args.help = true;
    else throw new Error(`unknown option: ${a}`);
  }
  return args;
}

function isDir(p) {
  try {
    return fs.statSync(p).isDirectory();
  } catch {
    return false;
  }
}

function printSetupHints(repo, capability) {
  for (const [, lines] of setupHintsForMissing(repo, capability)) {
    for (const line of lines) {
      console.log(line.startsWith("    ") ? line : `  ${line}`);
    }
  }
}

// Report every source that has a code graph ready. True if at least one is.
function checkCodeGraph(repo) {
  const ready = resolveAllReady(repo, "code_graph");
  if (ready.length === 0) {
    console.log("MISSING  code graph   (no registered source has one built)");
    listKnownGraphDirs(repo);
    console.log("  Build a code graph from any one configured source, then re-run. Options:");
    printSetupHints(repo, "code_graph");
    console.log(
      "  Do not write documentation from directory names or guesswork while this is missing."
    );
    return false;
  }
  for (const [src, p] of ready) {
    const mechanism = READ_MECHANISM[src.readMode] || "";
    let suffix = mechanism ? `  [${mechanism}]` : "";
    const state = src.detect(repo);
    if (state.stale === true) {
      suffix += "  [STALE vs HEAD; refresh requires approval]";
    }
    console.log(
      `READY    code graph   -> ${relativeDisplayPath(p, repo)}  (source: ${src.name})${suffix}`
    );
  }
  if (ready.length > 1) {
    console.log(
      `  ${ready.length} sources are ready — ask the user which should be ` +
        "primary; select by the evidence need in references/graph-sources.md."
    );
  }
  return true;
}

// Resolve the flow graph. Returns 'native', 'derived', or 'none' and prints a
// status line. Does not itself decide the exit code.
function reportFlowGraph(repo) {
  const ready = resolveAllReady(repo, "flow_graph");
  if (ready.length > 0) {
    for (const [src, p] of ready) {
      console.log(
        `READY    flow graph   -> ${relativeDisplayPath(p, repo)}  (source: ${src.name}, authoritative)`
      );
    }
    return "native";
  }
  const derived = findGraphFile(repo, DERIVED_FLOW_CANDIDATES);
  if (derived) {
    console.log(
      `READY    flow graph   -> ${relativeDisplayPath(derived, repo)}  (docforge-derived, provisional)`
    );
    return "derived";
  }
  console.log("MISSING  flow graph   (no native flow graph; none derived yet)");
  return "none";
}

function printFlowRemediation(repo) {
  console.log(
    "  A selected catalog entry requires the flow graph. Resolve either way:"
  );
  console.log(
    "  (a) Derive a provisional flow graph from the code graph " +
      "(see references/flow-derivation.md):"
  );
  console.log("    node scripts/derive_flow_graph.js prepare --repo <path>");
  console.log("    # dispatch the Docforge flow analyzer on the emitted context, then");
  console.log("    node scripts/derive_flow_graph.js write --repo <path> --analysis <analysis.json>");
  console.log("    # writes .docforge/tmp/flow-graph.json — provisional, never committed");
  console.log("  (b) Or produce a native (authoritative) flow graph from a source:");
  printSetupHints(repo, "flow_graph");
}

function main() {
  let args;
  try {
    args = parseArgs(process.argv.slice(2));
  } catch (error) {
    console.error(`error: ${error.message}`);
    return 2;
  }
  if (args.help) {
    console.log("usage: precheck_graph.js --repo <path> [--need code|flow]");
    return 0;
  }
  if (!args.repo) {
    console.error("usage: precheck_graph.js --repo <path> [--need code|flow]");
    return 2;
  }
  const need = args.need;
  if (need !== "code" && need !== "flow") {
    console.error(`--need must be 'code' or 'flow', got '${args.need}'`);
    return 2;
  }
  if (!isDir(args.repo)) {
    console.error(`Not a directory: ${args.repo}`);
    return 2;
  }

  const codeOk = checkCodeGraph(args.repo);
  const flowState = need === "flow" || codeOk ? reportFlowGraph(args.repo) : "none";

  console.log();
  if (!codeOk) {
    console.log(
      "BLOCKED. A code graph is docforge's universal precondition — no " +
        "documentation of any kind may be written until one exists. Tell the " +
        "user which source to build it with (options above); docforge never " +
        "fabricates a code graph itself."
    );
    return 1;
  }

  if (need === "code") {
    console.log("Code graph present — proceed.");
    if (flowState === "none") {
      console.log(
        "Note: no flow graph yet. Selected flow, Business Analyst, and " +
          "agent flow/glossary documents will resolve it when reached " +
          "(--need flow); other documents may proceed."
      );
    }
    return 0;
  }

  // need === "flow"
  if (flowState !== "none") {
    console.log("Code and flow graphs present — proceed.");
    if (flowState === "derived") {
      console.log(
        "Note: flows are docforge-derived (provisional). Confirm business " +
          "rules against source before asserting them; a native flow graph is " +
          "authoritative where available."
      );
    }
    return 0;
  }

  console.log("Code graph present, but flows are required for this plan and none exist yet.");
  printFlowRemediation(args.repo);
  return 1;
}

process.exit(main());
