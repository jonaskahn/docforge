#!/usr/bin/env node
"use strict";
/* Gate all docforge documentation work on the analysis it depends on.
 *
 * Both the knowledge graph and domain graph are required for every docforge
 * invocation — there is no fallback, no inspection substitute. This script
 * checks that the two files exist under .ua/ (or the legacy
 * .understand-anything/) and refuses to report READY unless both are
 * present. It does not care which tool produced them.
 *
 * understand-anything is the default producer, but this script also detects
 * a GitNexus index (.gitnexus/meta.json) and, when the graph is missing but
 * an index exists, points at the GitNexus bridge (graph_source_gitnexus.js
 * build, documented in references/gitnexus-bridge.md) instead of only
 * suggesting /understand. Priority is always: use .ua/*.json if present,
 * regardless of which source could also build it; only fall back to a
 * source-specific build suggestion when the files are actually missing. See
 * references/graph-sources.md for the full capability-to-source dispatch
 * table, and the comment in graph_source_gitnexus.js for why this can't be a
 * fully automatic build (MCP tool calls are agent-mediated, not scriptable).
 *
 * This script cannot check whether the understand-anything skill/plugin
 * itself is installed (that's a property of the calling agent's
 * environment, not this repo's filesystem) — the agent must confirm that
 * separately by checking its own skill listing or attempting `/understand`
 * and `/understand-domain`.
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
const { display, showGraphDirs } = require("./graph_common.js");
const { detect: gitnexusDetect } = require("./graph_source_gitnexus.js");
const { detect: uaDetect } = require("./graph_source_ua.js");

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

function isDir(p) {
  try {
    return fs.statSync(p).isDirectory();
  } catch {
    return false;
  }
}

const GITNEXUS_BUILD_CMD =
  "    node scripts/graph_source_gitnexus.js build --repo <path> " +
  "--nodes <nodes.json> --edges <edges.json> --processes <processes.json>";

// Print the Fix: block for a missing graph file. Always shows both
// remediation paths — understand-anything and GitNexus — since either one
// resolves the gap and the user may already have one but not the other
// installed. The GitNexus option's exact steps depend on whether an index
// already exists.
function printMissingRemediation(repo, gxIndex, { isDomain }) {
  if (isDomain) {
    console.log("  Fix (understand-anything): after the knowledge graph exists, run:");
    console.log("    /understand-domain");
    console.log(
      "  Business flows, docs/flows/, docs/product/overview.md and the " +
        "BA/PO overlays are never hand-typed. Do not enumerate flows from " +
        "route files or folder names as a substitute for this graph."
    );
  } else {
    console.log(
      "  Fix (understand-anything): confirm the understand-anything skill is " +
        "loaded in this session (check the skill listing, or load/invoke it), " +
        "then run:"
    );
    console.log("    /understand");
  }

  if (gxIndex) {
    console.log(
      `  Fix (GitNexus, index already found at ${display(gxIndex, repo)}): ` +
        "follow references/gitnexus-bridge.md, then run:"
    );
    console.log(GITNEXUS_BUILD_CMD);
  } else {
    console.log("  Fix (GitNexus, not yet installed/indexed): from the repo root, run:");
    console.log("    npx gitnexus analyze");
    console.log("    npx gitnexus setup");
    console.log("  Then follow references/gitnexus-bridge.md and run:");
    console.log(GITNEXUS_BUILD_CMD);
  }

  if (!isDomain) {
    console.log(
      "  Do not proceed to writing documentation from directory names or " +
        "guesswork while this is missing."
    );
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
  const ua = uaDetect(args.repo);

  const kg = ua.knowledgeGraph;
  if (kg) {
    console.log(`READY  knowledge graph  -> ${display(kg, args.repo)}`);
  } else {
    ok = false;
    console.log("MISSING  knowledge graph  (checked .ua/ and .understand-anything/)");
    showGraphDirs(args.repo);
    const gx = gitnexusDetect(args.repo);
    printMissingRemediation(args.repo, gx.index, { isDomain: false });
  }

  if (args.need === "domain") {
    const dg = ua.domainGraph;
    if (dg) {
      console.log(`READY  domain graph     -> ${display(dg, args.repo)}`);
    } else {
      ok = false;
      console.log("MISSING  domain graph  (checked .ua/ and .understand-anything/)");
      showGraphDirs(args.repo);
      const gx = gitnexusDetect(args.repo);
      printMissingRemediation(args.repo, gx.index, { isDomain: true });
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
