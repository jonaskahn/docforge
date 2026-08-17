"use strict";
/** The shared entry-surface vocabulary: which names, paths, and graph layers
 * read as "a flow starts here". Internal only: no CLI launcher.
 *
 * flow_index.js and graph_source_understand_anything.js both need this and
 * used to carry byte-identical private copies, which drifted — the layer list
 * in particular was narrower on the flow_index side. One definition now,
 * required by both.
 *
 * ENTRY_LAYER_WORDS is deliberately broad: a layer named "Screens & Routes" is
 * as much an entry surface as one named "API", and a frontend repo has no
 * layer matching "service" or "api" at all. Matching is substring-on-lowercase,
 * so "routes", "Screens & Routes", and "Route Handlers" all hit "route".
 */

// Verb prefixes that read as "this function starts something". ENTRY_WORDS is
// the permissive set (used with a path signal); CORE_ENTRY_WORDS is the strict
// subset (used when only layer membership backs the guess), so a bare `getFoo`
// in a service layer does not become a flow candidate on its own.
const ENTRY_WORDS = /^(?:[Aa]ggregate|[Tt]rack|[Pp]ublish|[Dd]ispatch|[Ee]xecute|[Rr]un|[Ss]tart|[Rr]eceive|[Pp]rocess|[Cc]onsume|[Hh]andle|[Cc]reate|[Uu]pdate|[Dd]elete|[Ss]ave|[Gg]et|[Pp]ost|[Pp]ut|[Pp]atch|[Ss]end)(?:[A-Z0-9_]|$)/;
const CORE_ENTRY_WORDS = /^(?:[Aa]ggregate|[Tt]rack|[Pp]ublish|[Dd]ispatch|[Ee]xecute|[Rr]un|[Ss]tart|[Rr]eceive|[Pp]rocess|[Cc]onsume|[Hh]andle)(?:[A-Z0-9_]|$)/;
// Class/symbol suffixes that name an entry surface outright.
const SURFACE_WORDS = /(controller|handler|processor|consumer|listener|worker|job|command|aggregator)$/i;
// Directory segments that put a file on an entry surface.
const PATH_WORDS = /(controllers?|handlers?|processors?|consumers?|workers?|jobs?|commands?|aggregators?|routes?|endpoints?)/i;

// Graph-layer name fragments that mark a layer as an entry/business surface.
// Backend vocabulary first, then the frontend surfaces a service-only list
// misses entirely — screens and routes are where a UI flow begins, and
// state/context layers are where it continues.
const ENTRY_LAYER_WORDS = [
  "service", "business", "domain", "application", "presentation", "api",
  "screen", "route", "page", "view", "controller", "handler",
  "state", "context", "store",
];

/** True when a graph layer's name reads as an entry/business surface. */
function isEntryLayer(name) {
  const lowered = String(name || "").toLowerCase();
  return ENTRY_LAYER_WORDS.some((word) => lowered.includes(word));
}

module.exports = {
  ENTRY_WORDS,
  CORE_ENTRY_WORDS,
  SURFACE_WORDS,
  PATH_WORDS,
  ENTRY_LAYER_WORDS,
  isEntryLayer,
};
