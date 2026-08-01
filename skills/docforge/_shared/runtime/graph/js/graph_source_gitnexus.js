#!/usr/bin/env node
"use strict";
/* GitNexus graph source: detection only.
 *
 * GitNexus (https://github.com/abhigyanpatwari/GitNexus) stores its graph in a
 * LadybugDB property-graph database at .gitnexus/lbug, with a sidecar
 * .gitnexus/gitnexus.json (legacy .gitnexus/meta.json) describing the index.
 * Docforge reads that database **directly**,
 * in place — there is no copy-to-JSON bridge:
 *
 *   - primary: the gitnexus MCP tools (`cypher`, `query`, `context`) and
 *     `gitnexus://repo/{name}/...` resources, available when the plugin loads;
 *   - offline: runtime/cli/{python,js}/graph_source_gitnexus_reader.{py,js}, which opens
 *     .gitnexus/lbug via @ladybugdb/core (Node) / the ladybug Python binding.
 *
 * Because GitNexus carries native Process nodes (execution flows) and Community
 * clusters (functional areas), it satisfies both the code-graph and the
 * flow-graph capability the moment its index exists — no derivation, no build.
 *
 * So this module is pure detection. See references/graph/graph-source-gitnexus.md for
 * the read recipes and references/graph/graph-sources.md for the capability dispatch.
 *
 * This module exposes a SOURCE descriptor consumed by the
 * graph_source_registry.js registry; see references/graph/adding-a-graph-source.md.
 *
 * Usage:
 *   node graph_source_gitnexus.js detect --repo <path>
 *
 * Node.js built-ins only.
 */

const fs = require("fs");
const cp = require("child_process");
const { findGraphFile, relativeDisplayPath } = require("./graph_storage.js");

const SOURCE_NAME = "gitnexus";
const DISPLAY = "GitNexus";
const CAPABILITIES = ["code_graph", "flow_graph"];
// A ladybug DB, not a JSON file: read via the gitnexus MCP or the offline
// reader (graph_source_gitnexus_reader.js), never via read_graph.js.
const READ_MODE = "db";

const LBUG_CANDIDATES = [".gitnexus/lbug"];
const INDEX_MARKER_CANDIDATES = [
  ".gitnexus/gitnexus.json",
  ".gitnexus/meta.json",
];

function gitHead(repo) {
  try {
    const out = cp.execFileSync("git", ["-C", repo, "rev-parse", "HEAD"], {
      encoding: "utf-8",
      timeout: 5000,
      stdio: ["ignore", "pipe", "ignore"],
    });
    return out.trim();
  } catch {
    return null;
  }
}

function readMeta(indexPath) {
  try {
    return JSON.parse(fs.readFileSync(indexPath, "utf-8"));
  } catch {
    return null;
  }
}

// Report the GitNexus graph's readiness, read directly from disk. Returns the
// registry-standard keys code_graph / flow_graph — each the path to the
// ladybug DB (.gitnexus/lbug) when that capability is available, or null —
// plus source-private fields: index, stats, stale. The DB satisfies code_graph
// when it has nodes and flow_graph when it has processes; when the sidecar
// metadata carries no stats we do not second-guess a present DB.
function detect(repo) {
  const lbug = findGraphFile(repo, LBUG_CANDIDATES);
  const index = findGraphFile(repo, INDEX_MARKER_CANDIDATES);
  const meta = index ? readMeta(index) : null;
  const stats = meta && typeof meta === "object" && meta.stats && typeof meta.stats === "object"
    ? meta.stats
    : null;

  let stale = null;
  if (meta && typeof meta === "object" && meta.lastCommit) {
    const head = gitHead(repo);
    if (head) stale = head !== meta.lastCommit;
  }

  const hasNodes = stats === null || (stats.nodes ?? 0) > 0;
  const hasProcesses = stats === null || (stats.processes ?? 0) > 0;
  return {
    code_graph: lbug && hasNodes ? lbug : null,
    flow_graph: lbug && hasProcesses ? lbug : null,
    index,
    stats,
    stale,
  };
}

// Lines telling the user how to produce the missing graph with GitNexus. The
// right steps depend on whether an index exists and whether it is stale.
function setupHint(repo, gap) {
  const info = detect(repo);
  const { index, stale } = info;
  if (!index) {
    return [
      "GitNexus (no index yet): global MCP setup is user-run when needed:",
      "    npx gitnexus setup",
      "  After explicit approval, the agent may build the repo index with:",
      "    npx gitnexus analyze",
      "  Re-run detect to confirm READY (see references/graph/graph-source-gitnexus.md).",
    ];
  }
  if (stale) {
    return [
      "GitNexus (index is STALE — indexed lastCommit != current HEAD): ask explicit approval, then re-index:",
      "    npx gitnexus analyze",
      "  Then re-run detect (see references/graph/graph-source-gitnexus.md).",
    ];
  }
  return [
    "GitNexus index present and current — the ladybug DB (.gitnexus/lbug) is " +
      "ready. Read it via the gitnexus MCP, or offline with " +
      "runtime/cli/python/graph_source_gitnexus_reader.js (references/graph/graph-source-gitnexus.md).",
  ];
}

function parseArgs(argv) {
  const args = { _: [] };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--repo") args.repo = argv[++i];
    else args._.push(a);
  }
  return args;
}

function runDetect(args) {
  const result = detect(args.repo);
  if (result.index || result.code_graph) {
    const target = result.code_graph || result.index;
    const stale = result.stale ? " (STALE vs HEAD)" : "";
    console.log(`READY  gitnexus  -> ${relativeDisplayPath(target, args.repo)}${stale}`);
    if (result.stats) {
      const s = result.stats;
      console.log(
        `  stats: ${s.nodes ?? "?"} nodes, ${s.edges ?? "?"} edges, ${s.processes ?? "?"} processes`
      );
    }
    console.log(
      "  Read via the gitnexus MCP, or offline with " +
        "runtime/cli/python/graph_source_gitnexus_reader.js."
    );
    return 0;
  }
  console.log("MISSING  gitnexus index  (checked for .gitnexus/lbug and current/legacy metadata)");
  for (const line of setupHint(args.repo, "code_graph")) {
    console.log(line.startsWith("    ") ? line : `  ${line}`);
  }
  return 1;
}

function main() {
  const argv = process.argv.slice(2);
  const command = argv[0];
  const args = parseArgs(argv.slice(1));

  if (command !== "detect") {
    console.error("usage: graph_source_gitnexus.js detect --repo <path>");
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
  return runDetect(args);
}

const SOURCE = {
  name: SOURCE_NAME,
  display: DISPLAY,
  capabilities: CAPABILITIES,
  readMode: READ_MODE,
  detect,
  setupHint,
};

module.exports = {
  main,
  SOURCE_NAME,
  DISPLAY,
  CAPABILITIES,
  READ_MODE,
  LBUG_CANDIDATES,
  INDEX_MARKER_CANDIDATES,
  detect,
  setupHint,
  SOURCE,
};

if (require.main === module) {
  process.exit(main());
}
