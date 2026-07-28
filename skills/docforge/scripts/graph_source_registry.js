#!/usr/bin/env node
"use strict";
/* Graph source registry — the single ordered list of graph producers docforge
 * knows about, plus the helpers that resolve a capability to a concrete graph.
 *
 * This is the whole extensibility surface on the script side: to add a source
 * (codegraph, graphify, …) write a graph_source_<name>.js exposing a SOURCE
 * descriptor and append it to SOURCES here — nothing else in precheck_graph.js
 * or read_graph.js changes. See references/adding-a-graph-source.md.
 *
 * A SOURCE descriptor is an object:
 *   {
 *     name,                       // stable id, e.g. "understand-anything"
 *     display,                    // human label
 *     capabilities: [..],         // subset of ["code_graph", "flow_graph"]
 *     readMode,                   // "json" (read with read_graph.js), "db"
 *                                 //   (query via a native interface / optional
 *                                 //   offline reader), or "mcp" (query via a
 *                                 //   native interface only — no offline reader)
 *     detect(repo) -> { code_graph: path|null, flow_graph: path|null, ... },
 *     setupHint(repo, gap) -> [lines],
 *     entryPoints(repo) -> [seeds]   // OPTIONAL
 *   }
 *
 * The optional entryPoints() hook returns ranked flow-derivation seeds —
 * [{id, name, kind, path, rank}], highest rank first — read from the source's
 * own entry-point signal (routes, exported-uncalled functions, entry-point
 * tags…), never a full scan. derive_flow_graph uses it to build an
 * entry-point-first, main-flow-first context instead of dumping the whole
 * graph; a source without it falls back to the flat dump. See
 * references/flow-derivation.md.
 *
 * Capabilities:
 *   code_graph  — structure and call/import relationships. Docforge's universal precondition.
 *   flow_graph  — business flows and ordered steps. Optional per source; if no
 *                 source supplies one, docforge derives a provisional one from
 *                 the code graph (see derive_flow_graph.js).
 *
 * Node.js built-ins only.
 */

const { SOURCE: understandAnythingSource } = require("./graph_source_understand_anything.js");
const { SOURCE: gitnexusSource } = require("./graph_source_gitnexus.js");
const { SOURCE: codegraphSource } = require("./graph_source_codegraph.js");

// Priority order: the first source that resolves a capability wins when the
// caller wants a single answer. resolveAllReady() exposes every ready source
// so the orchestrator can let the user choose.
const SOURCES = [understandAnythingSource, gitnexusSource, codegraphSource];

function sourcesProviding(capability) {
  return SOURCES.filter((source) => source.capabilities.includes(capability));
}

// Return [source, path] for the first source that actually has `capability`
// built on disk, else [null, null]. Never triggers a build.
function resolveFirstReady(repo, capability) {
  for (const source of sourcesProviding(capability)) {
    const found = source.detect(repo)[capability];
    if (found) return [source, found];
  }
  return [null, null];
}

// Every source that actually has `capability` on disk, in priority order, as
// [source, path] pairs. Empty when none is ready. Lets the caller present a
// choice when more than one source is available for the same repo.
function resolveAllReady(repo, capability) {
  const ready = [];
  for (const source of sourcesProviding(capability)) {
    const found = source.detect(repo)[capability];
    if (found) ready.push([source, found]);
  }
  return ready;
}

// For a miss: every capable source paired with its remediation block.
function setupHintsForMissing(repo, capability) {
  return sourcesProviding(capability).map((source) => [source, source.setupHint(repo, capability)]);
}

module.exports = {
  SOURCES,
  sourcesProviding,
  resolveFirstReady,
  resolveAllReady,
  setupHintsForMissing,
};
