#!/usr/bin/env node
"use strict";
/* Source-agnostic helpers shared by every graph_source_*.js module and by
 * check_preconditions.js.
 *
 * Nothing in this file knows which tool (understand-anything, GitNexus, or
 * any future source) produced a graph — it only knows how to find, display,
 * sanity check, and write the two on-disk files docforge itself reads:
 * $PROJECT_ROOT/.ua/knowledge-graph.json and $PROJECT_ROOT/.ua/domain-graph.json
 * (or their legacy .understand-anything/ counterparts, for reading only — new
 * writes always go to .ua/).
 *
 * Node.js built-ins only.
 */

const fs = require("fs");
const path = require("path");

const GRAPH_DIR_NAMES = [".ua", ".understand-anything"];

function isFile(p) {
  try {
    return fs.statSync(p).isFile();
  } catch {
    return false;
  }
}

function isDir(p) {
  try {
    return fs.statSync(p).isDirectory();
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

// Search the repo root, then every ancestor up to (and including) the git
// root, for the first candidate relative path that exists as a file.
function find(repo, candidates) {
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

function display(found, repo) {
  const base = path.resolve(repo);
  const rel = path.relative(base, found);
  return rel.startsWith("..") ? found : rel;
}

function showGraphDirs(repo) {
  const base = path.resolve(repo);
  let listed = false;
  for (const cur of [base, ...parents(base)]) {
    for (const name of GRAPH_DIR_NAMES) {
      const d = path.join(cur, name);
      if (isDir(d)) {
        let names;
        try {
          names = fs.readdirSync(d).sort();
        } catch (e) {
          names = [`(error listing: ${e.message})`];
        }
        console.log(
          `  ${name}/ exists at ${display(d, repo)} — contains: ${
            names.join(", ") || "(empty)"
          }`
        );
        listed = true;
      }
    }
    if (fs.existsSync(path.join(cur, ".git"))) break;
  }
  if (listed) {
    console.log("  Diagnose: node scripts/validate_graphs.js --repo . --verbose");
  }
}

// Minimal sanity check for a freshly-built knowledge graph, before it is
// written to disk. Returns an error string, or null if the shape is
// acceptable. Deliberately loose — docforge's own reader (graph_extract.js)
// already tolerates several key names; this only catches a build gone
// obviously wrong (empty or malformed), not schema drift.
function validateKnowledgeGraphShape(obj) {
  if (typeof obj !== "object" || obj === null || Array.isArray(obj)) {
    return "knowledge graph must be a JSON object";
  }
  if (!Array.isArray(obj.nodes) || obj.nodes.length === 0) {
    return "knowledge graph must have a non-empty 'nodes' list";
  }
  if (!Array.isArray(obj.edges)) {
    return "knowledge graph must have an 'edges' list (may be empty)";
  }
  return null;
}

// domain-graph.json has no rigid consumer today (no docforge script parses
// it directly) — only confirm it is a non-empty JSON object.
function validateDomainGraphShape(obj) {
  if (
    typeof obj !== "object" ||
    obj === null ||
    Array.isArray(obj) ||
    Object.keys(obj).length === 0
  ) {
    return "domain graph must be a non-empty JSON object";
  }
  return null;
}

// Write both graph files to $PROJECT_ROOT/.ua/, creating the directory if
// needed. Throws if either shape fails its sanity check — callers should
// surface that message and write nothing.
function writeGraph(repo, knowledgeGraph, domainGraph) {
  const kgError = validateKnowledgeGraphShape(knowledgeGraph);
  if (kgError) throw new Error(`refusing to write knowledge graph: ${kgError}`);
  const dgError = validateDomainGraphShape(domainGraph);
  if (dgError) throw new Error(`refusing to write domain graph: ${dgError}`);

  const uaDir = path.join(path.resolve(repo), ".ua");
  fs.mkdirSync(uaDir, { recursive: true });

  const kgPath = path.join(uaDir, "knowledge-graph.json");
  const dgPath = path.join(uaDir, "domain-graph.json");
  fs.writeFileSync(kgPath, JSON.stringify(knowledgeGraph, null, 2) + "\n", "utf-8");
  fs.writeFileSync(dgPath, JSON.stringify(domainGraph, null, 2) + "\n", "utf-8");
  return [kgPath, dgPath];
}

module.exports = {
  GRAPH_DIR_NAMES,
  find,
  display,
  showGraphDirs,
  validateKnowledgeGraphShape,
  validateDomainGraphShape,
  writeGraph,
};
