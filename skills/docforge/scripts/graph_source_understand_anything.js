#!/usr/bin/env node
"use strict";
/* understand-anything graph source: detection only.
 *
 * This source is always "already built" by the time docforge's Precheck sees
 * it — understand-anything writes .ua/knowledge-graph.json and
 * .ua/domain-graph.json (or the legacy .understand-anything/ path) itself,
 * via /understand and /understand-domain. There is no build() here, only
 * detect().
 *
 * Usage as a library:
 *   const { detect } = require("./graph_source_ua.js");
 *   const result = detect(repo); // { knowledgeGraph: path|null, domainGraph: path|null }
 *
 * Node.js built-ins only.
 */

const { find } = require("./graph_common.js");

const SOURCE_NAME = "understand-anything";

const KNOWLEDGE_GRAPH_CANDIDATES = [
  ".ua/knowledge-graph.json",
  ".understand-anything/knowledge-graph.json",
];

const DOMAIN_GRAPH_CANDIDATES = [
  ".ua/domain-graph.json",
  ".understand-anything/domain-graph.json",
];

function detect(repo) {
  return {
    knowledgeGraph: find(repo, KNOWLEDGE_GRAPH_CANDIDATES),
    domainGraph: find(repo, DOMAIN_GRAPH_CANDIDATES),
  };
}

module.exports = {
  SOURCE_NAME,
  KNOWLEDGE_GRAPH_CANDIDATES,
  DOMAIN_GRAPH_CANDIDATES,
  detect,
};
