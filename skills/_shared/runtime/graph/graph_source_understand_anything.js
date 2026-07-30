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
 * graph_source_registry.js registry; see references/graph/adding-a-graph-source.md
 * for the interface.
 *
 * Node.js built-ins only.
 */

const fs = require("fs");
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

// Tags that mark a re-export shim (index.js barrels), not real flow logic —
// excluded from entry-point seeds so they never crowd out true entry surfaces.
const NOISE_TAGS = new Set(["barrel", "re-export"]);
const ENTRY_NAME = /^(?:[Aa]ggregate|[Tt]rack|[Pp]ublish|[Dd]ispatch|[Ee]xecute|[Rr]un|[Ss]tart|[Rr]eceive|[Pp]rocess|[Cc]onsume|[Hh]andle|[Cc]reate|[Uu]pdate|[Dd]elete|[Ss]ave|[Gg]et|[Pp]ost|[Pp]ut|[Pp]atch|[Ss]end)(?:[A-Z0-9_]|$)/;
const CORE_ENTRY_NAME = /^(?:[Aa]ggregate|[Tt]rack|[Pp]ublish|[Dd]ispatch|[Ee]xecute|[Rr]un|[Ss]tart|[Rr]eceive|[Pp]rocess|[Cc]onsume|[Hh]andle)(?:[A-Z0-9_]|$)/;
const SURFACE_NAME = /(controller|handler|processor|consumer|listener|worker|job|command|aggregator)$/i;
const ENTRY_PATH = /(controllers?|handlers?|processors?|consumers?|workers?|jobs?|commands?|aggregators?|routes?|endpoints?)/i;

function detect(repo) {
  return {
    code_graph: findGraphFile(repo, CODE_GRAPH_CANDIDATES),
    flow_graph: findGraphFile(repo, FLOW_GRAPH_CANDIDATES),
  };
}

// Node ids belonging to a layer whose name reads as a service/business layer —
// a strong 'this is where flows live' signal in the UA graph.
function serviceLayerIds(doc) {
  const ids = new Set();
  const layers = doc && Array.isArray(doc.layers) ? doc.layers : [];
  for (const layer of layers) {
    if (!layer || typeof layer !== "object") continue;
    const name = String(layer.name || "").toLowerCase();
    if (["service", "business", "domain", "application", "presentation", "api"].some((word) => name.includes(word))) {
      for (const nid of layer.nodeIds || []) ids.add(nid);
    }
  }
  return ids;
}

// Ranked entry-point seeds for flow derivation, read from the UA code graph's
// own semantic signal — never a full-graph scan. Signal, in priority order
// (see references/graph/flow-derivation.md): api-handler tag > service/pipeline
// type > entry-point tag (minus barrels) > step type; each boosted by
// Service-layer membership and outgoing-edge fan-out. Returns [] when the
// graph carries no such signal, so the caller falls back to a full dump.
function entryPoints(repo) {
  const path = findGraphFile(repo, CODE_GRAPH_CANDIDATES);
  if (!path) return [];
  let doc;
  try {
    doc = JSON.parse(fs.readFileSync(path, "utf-8"));
  } catch {
    return [];
  }
  if (!doc || typeof doc !== "object") return [];

  const nodes = doc.nodes || [];
  const edges = doc.edges || [];
  const serviceIds = serviceLayerIds(doc);

  const fanout = new Map();
  for (const edge of edges) {
    if (edge && typeof edge === "object" && edge.source != null) {
      fanout.set(edge.source, (fanout.get(edge.source) || 0) + 1);
    }
  }

  const seeds = [];
  for (const node of nodes) {
    if (!node || typeof node !== "object") continue;
    const tags = new Set((node.tags || []).map((t) => String(t).toLowerCase()));
    const nodeType = String(node.type || "").toLowerCase();
    if ([...tags].some((t) => NOISE_TAGS.has(t))) continue;

    let tier;
    if (tags.has("api-handler")) tier = 1000;
    else if (nodeType === "service" || nodeType === "pipeline") tier = 800;
    else if (tags.has("entry-point")) tier = 600;
    else if (nodeType === "step") tier = 300;
    else if (
      (nodeType === "class"
        && SURFACE_NAME.test(String(node.name || ""))
        && (serviceIds.has(node.id) || ENTRY_PATH.test(String(node.filePath || "")))) ||
      (nodeType === "function"
        && ((ENTRY_PATH.test(String(node.filePath || "")) && ENTRY_NAME.test(String(node.name || "")))
          || (serviceIds.has(node.id) && CORE_ENTRY_NAME.test(String(node.name || "")))))
    ) {
      // Some UA graphs expose only file/class/function nodes and containment
      // edges. These are candidate entry signals, never native flow claims.
      tier = 200;
    }
    else continue;

    const nid = node.id;
    const rank = tier + (serviceIds.has(nid) ? 200 : 0) + (fanout.get(nid) || 0);
    seeds.push({
      id: nid,
      name: node.name,
      kind: node.type,
      path: node.filePath,
      rank,
    });
  }

  seeds.sort((a, b) => b.rank - a.rank);
  return seeds;
}

// Lines telling the user how to produce the missing graph with this source.
// `gap` is 'code_graph' or 'flow_graph'.
function setupHint(repo, gap) {
  if (gap === "flow_graph") {
    return [
      "Understand-Anything: after explicit approval and once the code graph exists, the agent may run:",
      "    /understand-domain",
    ];
  }
  return [
    "Understand-Anything: confirm the understand-anything skill is loaded " +
      "in this session. After disclosing first-run cost and receiving explicit approval, the agent may run:",
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
  entryPoints,
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
  entryPoints,
  SOURCE,
};
