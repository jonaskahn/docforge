#!/usr/bin/env node
"use strict";
/* Source-agnostic graph-file storage helpers shared by every graph_source_*.js
 * module, by the graph_source_registry.js registry, by precheck_graph.js, and
 * by derive_flow_graph.js.
 *
 * Nothing in this file knows which tool (understand-anything, GitNexus, or
 * any future source) produced a graph — it only knows how to find, display,
 * sanity check, and write graph files on disk. There is no single canonical
 * store: each source declares where its own graph lives (understand-anything
 * reads .ua/, GitNexus stores a ladybug DB under .gitnexus/, CodeGraph stores
 * a SQLite DB under .codegraph/, and docforge's own derived flow graph is
 * written to the never-committed .docforge/tmp/).
 *
 * Node.js built-ins only.
 */

const fs = require("fs");
const path = require("path");
const { ensureDocforgeGitignore, ensureGitignoredDir } = require("../../common/js/_util.js");

// Directories a graph file may live in, for diagnostics only. Detection
// itself is per-source (each source declares its own candidate paths); this
// list is used solely to list folder contents on a miss.
const KNOWN_GRAPH_DIRS = [".ua", ".understand-anything", ".gitnexus", ".codegraph", ".docforge/tmp"];

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
function findGraphFile(repo, candidates) {
  const base = path.resolve(repo);
  for (const current of [base, ...parents(base)]) {
    for (const relativePath of candidates) {
      const candidate = path.join(current, relativePath);
      if (isFile(candidate)) return candidate;
    }
    if (fs.existsSync(path.join(current, ".git"))) break;
  }
  return null;
}

function relativeDisplayPath(found, repo) {
  const base = path.resolve(repo);
  const rel = path.relative(base, found);
  return rel.startsWith("..") ? found : rel;
}

function listKnownGraphDirs(repo) {
  const base = path.resolve(repo);
  let listed = false;
  for (const current of [base, ...parents(base)]) {
    for (const name of KNOWN_GRAPH_DIRS) {
      const directory = path.join(current, name);
      if (isDir(directory)) {
        let names;
        try {
          names = fs.readdirSync(directory).sort();
        } catch (error) {
          names = [`(error listing: ${error.message})`];
        }
        console.log(
          `  ${name}/ exists at ${relativeDisplayPath(directory, repo)} — contains: ${
            names.join(", ") || "(empty)"
          }`
        );
        listed = true;
      }
    }
    if (fs.existsSync(path.join(current, ".git"))) break;
  }
  if (listed) {
    console.log("  Diagnose: node runtime/cli/js/diagnose_graphs.js --repo . --verbose");
  }
}

// Sanity check for a flow graph before it is written — today only
// docforge's own derivation writes one. It uses the docforge flow shape: a
// non-empty 'flows' list of objects, each with a 'name' and a 'steps' list.
// Refusing an empty graph is what stops a derivation gone wrong from
// masquerading as a real flow graph.
function validateFlowGraphShape(flowGraph) {
  if (typeof flowGraph !== "object" || flowGraph === null || Array.isArray(flowGraph)) {
    return "flow graph must be a JSON object";
  }
  if (!Array.isArray(flowGraph.flows) || flowGraph.flows.length === 0) {
    return "flow graph must have a non-empty 'flows' list";
  }
  for (let index = 0; index < flowGraph.flows.length; index++) {
    const flow = flowGraph.flows[index];
    if (typeof flow !== "object" || flow === null || Array.isArray(flow) || !flow.name) {
      return `flow[${index}] must be an object with a non-empty 'name'`;
    }
    if (!Array.isArray(flow.steps)) {
      return `flow[${index}] ('${flow.name}') must have a 'steps' list`;
    }
  }
  return null;
}

function writeJson(p, graph) {
  fs.mkdirSync(path.dirname(p), { recursive: true });
  fs.writeFileSync(p, JSON.stringify(graph, null, 2) + "\n", "utf-8");
}

// Write a flow graph to $PROJECT_ROOT/<destRel>/flow-graph.json.
// Docforge's derivation passes destRel='.docforge/tmp' (never committed).
function writeFlowGraph(repo, flowGraph, destRel = ".docforge/tmp") {
  const error = validateFlowGraphShape(flowGraph);
  if (error) throw new Error(`refusing to write flow graph: ${error}`);
  const p = path.join(path.resolve(repo), destRel, "flow-graph.json");
  writeJson(p, flowGraph);
  return p;
}

// Drop $PROJECT_ROOT/.docforge/tmp/.gitignore containing '*' so the
// provisional derived flow graph is never committed. Idempotent.
function ensureTmpDirGitignored(repo) {
  ensureDocforgeGitignore(path.join(path.resolve(repo), ".docforge"));
  return ensureGitignoredDir(path.join(path.resolve(repo), ".docforge", "tmp"));
}

module.exports = {
  KNOWN_GRAPH_DIRS,
  findGraphFile,
  relativeDisplayPath,
  listKnownGraphDirs,
  validateFlowGraphShape,
  writeJson,
  writeFlowGraph,
  ensureTmpDirGitignored,
};
