#!/usr/bin/env node
"use strict";
/* CodeGraph graph source: detection only.
 *
 * CodeGraph (https://github.com/colbymchenry/codegraph) indexes a repo into a
 * SQLite database at .codegraph/codegraph.db. Unlike GitNexus, it is
 * **MCP-only** — there is no JSON export and no offline reader docforge can
 * open directly:
 *
 *   - the codegraph MCP tool (`codegraph_explore`), available once
 *     `codegraph install` has wired the MCP server into the calling agent
 *     and `codegraph init` has built the index for this repo. There is
 *     nothing else — no graph_source_codegraph_reader.{py,js} exists, and
 *     none is planned.
 *
 * CodeGraph's own file watcher keeps the index synced on every save
 * (debounced auto-sync) and reconciles it at MCP-connect time, so unlike
 * GitNexus this module does not compute staleness against git HEAD — a
 * present db is current by construction.
 *
 * CodeGraph carries no business-flow/process concept (it is a structural
 * call/import/symbol graph only), so it satisfies only the code-graph
 * capability, never flow-graph.
 *
 * Readiness here is only half the picture. detect() can confirm the db file
 * exists on disk, but it cannot see whether codegraph_explore is actually
 * wired into the calling agent's session — only the agent knows its own
 * tool list. So "READY" from this module means "an index exists to query,"
 * not "you can query it right now." Before treating a codegraph result as
 * usable, the agent must confirm codegraph_explore (possibly deferred) is
 * present in this session's tools; if it is absent entirely, tell the user
 * to run `codegraph install` and restart the agent — see
 * references/graph/graph-source-codegraph.md.
 *
 * This module exposes a SOURCE descriptor consumed by the
 * graph_source_registry.js registry; see references/graph/adding-a-graph-source.md.
 *
 * Usage:
 *   node graph_source_codegraph.js detect --repo <path>
 *
 * Node.js built-ins only.
 */

const fs = require("fs");
const { findGraphFile, relativeDisplayPath } = require("./graph_storage.js");

const SOURCE_NAME = "codegraph";
const DISPLAY = "CodeGraph";
const CAPABILITIES = ["code_graph"];
// A SQLite DB queried exclusively through the codegraph MCP tool — no JSON
// export, no offline reader. Distinct from GitNexus's "db" mode because
// there is no graph_source_codegraph_reader to fall back to.
const READ_MODE = "mcp";

const DB_CANDIDATES = [".codegraph/codegraph.db"];

// Report whether a CodeGraph index exists on disk. Returns the
// registry-standard keys code_graph / flow_graph — code_graph is the path to
// .codegraph/codegraph.db when present, else null; flow_graph is always null
// (CodeGraph has no business-flow/process capability). Pure filesystem
// check, no staleness computation — CodeGraph's own auto-sync watcher and
// connect-time reconciliation already keep a present db current.
function detect(repo) {
  const db = findGraphFile(repo, DB_CANDIDATES);
  return {
    code_graph: db,
    flow_graph: null,
  };
}

// Lines explaining global setup separately from approved repo indexing.
function setupHint(repo, _gap) {
  const db = detect(repo).code_graph;
  if (!db) {
    return [
      "CodeGraph (no index yet): global setup is user-run:",
      "    codegraph install   # one-time MCP wiring; restart the agent afterward",
      "  Once the tool is wired, ask explicit approval; the agent may then run:",
      "    codegraph init      # builds .codegraph/codegraph.db for this repo",
      "  Re-run detect to confirm READY (see references/graph/graph-source-codegraph.md).",
    ];
  }
  return [
    "CodeGraph index present — .codegraph/codegraph.db is ready. Before " +
      "reading it, confirm the codegraph_explore MCP tool (possibly listed as " +
      "deferred) is actually in this session's tool list — a present db does " +
      "not by itself mean the MCP server is wired to this agent.",
    "  If codegraph_explore is listed: load it (via tool search if deferred) and query it directly.",
    "  If it is not listed at all: ask the user to run `codegraph install` " +
      "outside this agent, then restart. There is no offline reader to fall " +
      "back to (see references/graph/graph-source-codegraph.md).",
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
  const db = detect(args.repo).code_graph;
  if (db) {
    console.log(`READY  codegraph  -> ${relativeDisplayPath(db, args.repo)}`);
    console.log(
      "  On-disk index found. This does NOT confirm the codegraph_explore " +
        "MCP tool is wired to the calling agent this session — check the " +
        "tool list separately before reading."
    );
    return 0;
  }
  console.log("MISSING  codegraph index  (checked for .codegraph/codegraph.db)");
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
    console.error("usage: graph_source_codegraph.js detect --repo <path>");
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

/** Ranked flow-derivation seeds, read structurally from the db.
 *
 * Kept as a thin delegate so the reader (and its node:sqlite dependency) is
 * only required when a caller actually asks for seeds. Returns [] when the db
 * is absent or its schema is newer than the reader knows, which is what makes
 * the MCP-only fallback automatic. */
function entryPoints(repo) {
  return require("./graph_source_codegraph_reader.js").entryPoints(repo);
}

const SOURCE = {
  name: SOURCE_NAME,
  display: DISPLAY,
  capabilities: CAPABILITIES,
  readMode: READ_MODE,
  detect,
  setupHint,
  // Structure (ranked entries, ordered call chains) is read from the db;
  // semantics still come from codegraph_explore. Without this hook
  // derive_flow_graph had no data at all for CodeGraph repos.
  entryPoints,
};

module.exports = {
  main,
  SOURCE_NAME,
  DISPLAY,
  CAPABILITIES,
  READ_MODE,
  DB_CANDIDATES,
  detect,
  setupHint,
  entryPoints,
  SOURCE,
};

if (require.main === module) {
  process.exit(main());
}
