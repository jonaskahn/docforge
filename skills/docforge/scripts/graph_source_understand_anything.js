#!/usr/bin/env node
"use strict";
/* understand-anything graph source: detection only.
 *
 * understand-anything writes .ua/knowledge-graph.json (code graph) and
 * .ua/domain-graph.json (flow graph) itself — or the legacy
 * .understand-anything/ path — via /understand and /understand-domain.
 * docforge reads those files directly (zero-copy), so there is no build()
 * here, only detect() and the setup hints for when a needed graph is absent.
 *
 * This module exposes a SOURCE descriptor consumed by the
 * graph_source_registry.js registry; see references/adding-a-graph-source.md
 * for the interface.
 *
 * Node.js built-ins only.
 */

const { findGraphFile } = require("./graph_storage.js");

const SOURCE_NAME = "understand-anything";
const DISPLAY = "Understand-Anything";
const CAPABILITIES = ["code_graph", "flow_graph"];
// JSON graphs on disk: read offline with read_graph.js, no external interface.
const READ_MODE = "json";

const CODE_GRAPH_CANDIDATES = [
  ".ua/knowledge-graph.json",
  ".understand-anything/knowledge-graph.json",
];

const FLOW_GRAPH_CANDIDATES = [
  ".ua/domain-graph.json",
  ".understand-anything/domain-graph.json",
];

function detect(repo) {
  return {
    code_graph: findGraphFile(repo, CODE_GRAPH_CANDIDATES),
    flow_graph: findGraphFile(repo, FLOW_GRAPH_CANDIDATES),
  };
}

// Lines telling the user how to produce the missing graph with this source.
// `gap` is 'code_graph' or 'flow_graph'.
function setupHint(repo, gap) {
  if (gap === "flow_graph") {
    return [
      "Understand-Anything: after the code graph exists, run:",
      "    /understand-domain",
    ];
  }
  return [
    "Understand-Anything: confirm the understand-anything skill is loaded " +
      "in this session (check the skill listing, or load/invoke it), then run:",
    "    /understand   (or /understand <subdir> to scope; first runs on " +
      "large repos consume tokens — say so before starting)",
  ];
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
  SOURCE_NAME,
  DISPLAY,
  CAPABILITIES,
  READ_MODE,
  CODE_GRAPH_CANDIDATES,
  FLOW_GRAPH_CANDIDATES,
  detect,
  setupHint,
  SOURCE,
};
