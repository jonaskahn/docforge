#!/usr/bin/env node
"use strict";
/* Validate and report on graph files at repository root.
 *
 * Helps diagnose "graph not found" false positives when a graph folder exists
 * but scripts report graphs missing. Scans the known store locations — `.ua/`,
 * legacy `.understand-anything/`, `.gitnexus/` (GitNexus's ladybug DB),
 * `.codegraph/` (CodeGraph's SQLite DB), and `.docforge/tmp/`
 * (docforge-derived, provisional) — and reports:
 *   - which graph folders exist and what they contain
 *   - whether a code (knowledge) graph and a flow (domain) graph are present
 *   - file sizes and modification times
 *   - schema structure (nodes/edges count) for JSON graphs; a note for the
 *     binary ladybug/SQLite DBs (queried via their MCP tools, not read here)
 *
 * Usage:
 *   node diagnose_graphs.js --repo <path>
 *   node diagnose_graphs.js --repo <path> --verbose
 *
 * Node.js built-ins only.
 */

const fs = require("fs");
const path = require("path");
const { KNOWN_GRAPH_DIRS } = require("./graph_storage.js");

// code graph is the universal precondition; flow graph is optional (a source
// emits it, or docforge derives a provisional one into .docforge/tmp/).
// GitNexus's .gitnexus/lbug is a ladybug DB that serves both capabilities.
// CodeGraph's .codegraph/codegraph.db serves only the code graph — it has no
// flow_graph capability, so it is absent from the flow candidates below.
const GRAPH_CANDIDATES = {
  "code (knowledge) graph": [
    ".ua/knowledge-graph.json",
    ".understand-anything/knowledge-graph.json",
    ".gitnexus/lbug",
    ".codegraph/codegraph.db",
  ],
  "flow (domain) graph": [
    ".ua/domain-graph.json",
    ".understand-anything/domain-graph.json",
    ".gitnexus/lbug",
    ".docforge/tmp/flow-graph.json",
  ],
};
const REQUIRED = new Set(["code (knowledge) graph"]);

// Binary DB files probeGraph() cannot parse as JSON, and the note printed for
// each in --verbose output.
const DB_NOTES = {
  lbug: "ladybug DB (binary) — query via the gitnexus MCP or scripts/graph_source_gitnexus_reader.js",
  "codegraph.db":
    "SQLite DB (binary) — query via the codegraph MCP tool (codegraph_explore); no offline reader",
};

function parseArgs(argv) {
  const args = { verbose: false };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--repo") args.repo = argv[++i];
    else if (a === "--verbose") args.verbose = true;
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

function isFile(p) {
  try {
    return fs.statSync(p).isFile();
  } catch {
    return false;
  }
}

function parents(dir) {
  const out = [];
  let cur = dir;
  for (;;) {
    const up = path.dirname(cur);
    if (up === cur) break;
    out.push(up);
    cur = up;
  }
  return out;
}

function findGraph(repo, candidates) {
  const base = path.resolve(repo);
  for (const cur of [base, ...parents(base)]) {
    for (const rel of candidates) {
      const p = path.join(cur, rel);
      if (isFile(p)) return p;
    }
    if (fs.existsSync(path.join(cur, ".git"))) break;
  }
  return null;
}

function probeGraph(p) {
  if (Object.prototype.hasOwnProperty.call(DB_NOTES, path.basename(p))) {
    const stat = fs.statSync(p);
    return {
      database: true,
      size_bytes: stat.size,
      mtime: new Date(stat.mtimeMs).toISOString(),
    };
  }
  try {
    const raw = fs.readFileSync(p, "utf8");
    const data = JSON.parse(raw);
    const stat = fs.statSync(p);
    const info = {
      valid_json: true,
      size_bytes: stat.size,
      mtime: new Date(stat.mtimeMs).toISOString(),
    };
    for (const key of ["nodes", "files", "entities", "items"]) {
      if (Array.isArray(data[key])) {
        info.node_key = key;
        info.node_count = data[key].length;
        break;
      }
    }
    for (const key of ["edges", "links", "relationships", "flows"]) {
      if (Array.isArray(data[key])) {
        info.edge_key = key;
        info.edge_count = data[key].length;
        break;
      }
    }
    return info;
  } catch (e) {
    return { valid_json: false, error: e.message };
  }
}

function fmtSize(n) {
  return `${n.toLocaleString("en-US")} bytes`;
}

function fmtMtime(stat) {
  const d = new Date(stat.mtimeMs);
  const pad = (n) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(
    d.getHours()
  )}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`;
}

function listDir(repo, dir) {
  const rel = dir.startsWith(repo) ? path.relative(repo, dir) : dir;
  console.log(`Contents of ${rel}/:`);
  try {
    const items = fs.readdirSync(dir).sort();
    for (const name of items) {
      const full = path.join(dir, name);
      const stat = fs.statSync(full);
      const size = stat.isFile() ? fmtSize(stat.size) : "[dir]";
      console.log(`  ${name.padEnd(30)}  ${size.padEnd(15)}  ${fmtMtime(stat)}`);
    }
  } catch (e) {
    console.error(`  Error reading: ${e.message}`);
  }
  console.log();
}

function main() {
  const args = parseArgs(process.argv.slice(2));
  if (!args.repo) {
    console.error("usage: diagnose_graphs.js --repo <path> [--verbose]");
    return 2;
  }
  if (!isDir(args.repo)) {
    console.error(`Not a directory: ${args.repo}`);
    return 2;
  }

  const repo = path.resolve(args.repo);
  console.log(`Repository: ${repo}`);
  console.log();

  console.log("Folder status:");
  const presentDirs = [];
  for (const name of KNOWN_GRAPH_DIRS) {
    const d = path.join(repo, name);
    const exists = isDir(d);
    console.log(`  ${(name + "/").padEnd(28)}${exists ? " ✓ exists" : " ✗ missing"}`);
    if (exists) presentDirs.push(d);
  }
  console.log();

  for (const d of presentDirs) listDir(repo, d);

  console.log("Graph discovery (upward search from repo root):");
  let codeOk = true;
  for (const [graphName, candidates] of Object.entries(GRAPH_CANDIDATES)) {
    const tag = REQUIRED.has(graphName) ? "required" : "optional";
    const found = findGraph(repo, candidates);
    if (found) {
      const relPath = found.startsWith(repo) ? path.relative(repo, found) : found;
      console.log(`  ${graphName.padEnd(24)} (${tag})  ✓ found at ${relPath}`);
      if (args.verbose) {
        const info = probeGraph(found);
        if (info.database) {
          console.log(`    - size: ${fmtSize(info.size_bytes)}`);
          console.log(`    - mtime: ${info.mtime}`);
          console.log(`    - ${DB_NOTES[path.basename(found)] || "binary DB"}`);
        } else if (info.valid_json) {
          console.log(`    - size: ${fmtSize(info.size_bytes)}`);
          console.log(`    - mtime: ${info.mtime}`);
          if (info.node_key) console.log(`    - nodes (${info.node_key}): ${info.node_count ?? "?"}`);
          if (info.edge_key) console.log(`    - ${info.edge_key}: ${info.edge_count ?? "?"}`);
        } else {
          console.log(`    ⚠ Invalid JSON: ${info.error}`);
        }
      }
    } else {
      console.log(`  ${graphName.padEnd(24)} (${tag})  ✗ not found`);
      if (REQUIRED.has(graphName)) codeOk = false;
    }
  }

  console.log();
  if (codeOk) {
    console.log(
      "✓ Code graph present. (A flow graph is optional — a source may " +
        "emit one, or docforge derives a provisional one.)"
    );
    return 0;
  }
  console.log(
    "✗ No code graph found. Build one from any configured source — " +
      "see references/graph-sources.md."
  );
  return 1;
}

process.exit(main());
