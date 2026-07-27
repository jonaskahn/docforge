#!/usr/bin/env node
"use strict";
/* Validate and report on graph files at repository root.
 *
 * Helps diagnose "graph not found" false positives when .ua/ folder exists
 * but scripts report graphs missing. Scans for graph files and reports:
 *   - Whether .ua/ folder exists
 *   - What files are inside it
 *   - Whether knowledge-graph.json and domain-graph.json are present
 *   - File sizes and modification times
 *   - Schema structure (nodes count, etc.)
 *
 * Usage:
 *   node validate_graphs.js --repo <path>
 *   node validate_graphs.js --repo <path> --verbose
 *
 * Node.js built-ins only.
 */

const fs = require("fs");
const path = require("path");

const GRAPH_CANDIDATES = {
  "knowledge-graph.json": [".ua/knowledge-graph.json", ".understand-anything/knowledge-graph.json"],
  "domain-graph.json": [".ua/domain-graph.json", ".understand-anything/domain-graph.json"],
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
    for (const key of ["edges", "links", "relationships"]) {
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

function listDir(dir) {
  console.log(`Contents of ${path.basename(dir)}/:`);
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
    console.error("usage: validate_graphs.js --repo <path> [--verbose]");
    return 2;
  }
  if (!isDir(args.repo)) {
    console.error(`Not a directory: ${args.repo}`);
    return 2;
  }

  const repo = path.resolve(args.repo);
  console.log(`Repository: ${repo}`);
  console.log();

  const uaDir = path.join(repo, ".ua");
  const uaLegacy = path.join(repo, ".understand-anything");
  const hasUa = isDir(uaDir);
  const hasLegacy = isDir(uaLegacy);

  console.log("Folder status:");
  console.log(`  .ua/                     ${hasUa ? " ✓ exists" : " ✗ missing"}`);
  console.log(`  .understand-anything/    ${hasLegacy ? " ✓ exists" : " ✗ missing"}`);
  console.log();

  if (hasUa) listDir(uaDir);
  if (hasLegacy) listDir(uaLegacy);

  console.log("Graph discovery (upward search from repo root):");
  let allOk = true;

  for (const [graphName, candidates] of Object.entries(GRAPH_CANDIDATES)) {
    const found = findGraph(repo, candidates);
    if (found) {
      const relPath = found.startsWith(repo) ? path.relative(repo, found) : found;
      console.log(`  ${graphName.padEnd(25)}  ✓ found at ${relPath}`);
      if (args.verbose) {
        const info = probeGraph(found);
        if (info.valid_json) {
          console.log(`    - size: ${fmtSize(info.size_bytes)}`);
          console.log(`    - mtime: ${info.mtime}`);
          if (info.node_key) console.log(`    - nodes (${info.node_key}): ${info.node_count ?? "?"}`);
          if (info.edge_key) console.log(`    - edges (${info.edge_key}): ${info.edge_count ?? "?"}`);
        } else {
          console.log(`    ⚠ Invalid JSON: ${info.error}`);
        }
      }
    } else {
      console.log(`  ${graphName.padEnd(25)}  ✗ not found (checked .ua/ and .understand-anything/)`);
      allOk = false;
    }
  }

  console.log();
  if (allOk) {
    console.log("✓ All graphs found and accessible.");
    return 0;
  }
  console.log("✗ Some graphs missing. Run /understand and/or /understand-domain");
  return 1;
}

process.exit(main());
