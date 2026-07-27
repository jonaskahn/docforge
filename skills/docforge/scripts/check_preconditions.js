#!/usr/bin/env node
"use strict";
/* Gate all docforge documentation work on the analysis it depends on.
 *
 * Both the knowledge graph and domain graph are required for every docforge
 * invocation — there is no fallback, no inspection substitute. This script checks
 * that the two files exist and refuses to report READY unless both are present.
 * It cannot check whether the understand-anything skill/plugin itself is installed
 * (that's a property of the calling agent's environment, not this repo's filesystem)
 * — the agent must confirm that separately by checking its own skill listing or
 * attempting `/understand` and `/understand-domain`.
 *
 * Exit code 0 only when every file required for the requested --need scope is
 * present. Non-zero otherwise, with a specific remediation command per gap.
 *
 * Usage:
 *   node check_preconditions.js --repo <path> --need graph
 *   node check_preconditions.js --repo <path> --need domain
 *
 * Node.js built-ins only.
 */

const fs = require("fs");
const path = require("path");

const KNOWLEDGE_GRAPH_CANDIDATES = [
  ".ua/knowledge-graph.json",
  ".understand-anything/knowledge-graph.json",
];

const DOMAIN_GRAPH_CANDIDATES = [
  ".ua/domain-graph.json",
  ".understand-anything/domain-graph.json",
];

function parseArgs(argv) {
  const args = { need: "domain" };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--repo") args.repo = argv[++i];
    else if (a === "--need") args.need = argv[++i];
    else if (a === "-h" || a === "--help") args.help = true;
  }
  return args;
}

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

// Search the graph at the repo root, then every ancestor up to (and
// including) the git root — the graphs live at $PROJECT_ROOT/.ua/..., and a
// direct lookup from a subdirectory would otherwise falsely report "not found".
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
    for (const name of [".ua", ".understand-anything"]) {
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

function main() {
  const args = parseArgs(process.argv.slice(2));
  if (!args.repo) {
    console.error("usage: check_preconditions.js --repo <path> [--need graph|domain]");
    return 2;
  }
  if (!["graph", "domain"].includes(args.need)) {
    console.error(`--need must be 'graph' or 'domain', got '${args.need}'`);
    return 2;
  }
  if (!isDir(args.repo)) {
    console.error(`Not a directory: ${args.repo}`);
    return 2;
  }

  let ok = true;

  const kg = find(args.repo, KNOWLEDGE_GRAPH_CANDIDATES);
  if (kg) {
    console.log(`READY  knowledge graph  -> ${display(kg, args.repo)}`);
  } else {
    ok = false;
    console.log("MISSING  knowledge graph  (checked .ua/ and .understand-anything/)");
    showGraphDirs(args.repo);
    console.log(
      "  Fix: confirm the understand-anything skill is loaded in this session " +
        "(check the skill listing, or load/invoke it), then run:"
    );
    console.log("    /understand");
    console.log(
      "  Do not proceed to writing documentation from directory names or " +
        "guesswork while this is missing."
    );
  }

  if (args.need === "domain") {
    const dg = find(args.repo, DOMAIN_GRAPH_CANDIDATES);
    if (dg) {
      console.log(`READY  domain graph     -> ${display(dg, args.repo)}`);
    } else {
      ok = false;
      console.log("MISSING  domain graph  (checked .ua/ and .understand-anything/)");
      showGraphDirs(args.repo);
      console.log("  Fix: after the knowledge graph exists, run:");
      console.log("    /understand-domain");
      console.log(
        "  Business flows, docs/flows/, docs/product/overview.md and the " +
          "BA/PO overlays are never hand-typed. Do not enumerate flows from " +
          "route files or folder names as a substitute for this graph."
      );
    }
  }

  console.log();
  if (ok) {
    console.log("All required analysis present. Proceed.");
    return 0;
  }
  console.log(
    "BLOCKED. No documentation of any kind may be written until every " +
      "MISSING item above is resolved. Tell the user what is missing and which " +
      "command produces it. Both the knowledge graph and domain graph are " +
      "required for all docforge work — there is no inspection fallback or " +
      "substitute for either."
  );
  return 1;
}

process.exit(main());
