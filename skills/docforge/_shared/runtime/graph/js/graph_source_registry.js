#!/usr/bin/env node
"use strict";
/* Graph source registry — the single ordered list of graph producers docforge
 * knows about, plus the helpers that resolve a capability to a concrete graph.
 *
 * This is the whole extensibility surface on the script side: to add a source
 * (codegraph, graphify, …) write a graph_source_<name>.js exposing a SOURCE
 * descriptor and append it to SOURCES here — nothing else in precheck_graph.js
 * or read_graph.js changes. See references/graph/adding-a-graph-source.md.
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
 * references/graph/flow-derivation.md.
 *
 * Capabilities:
 *   code_graph  — structure and call/import relationships. Docforge's universal precondition.
 *   flow_graph  — business flows and ordered steps. Optional per source; if no
 *                 source supplies one, docforge derives a provisional one from
 *                 the code graph (see derive_flow_graph.js).
 *
 * Which resolver to call:
 *   resolveLocked()      what every step after `init` wants — honors the provider
 *                        the user chose and recorded in manifest["graph"], falling
 *                        back to priority order only when no lock exists.
 *   resolveFirstReady()  priority order, lock-blind. Only for callers that run
 *                        *before* a lock exists, or that deliberately ignore it.
 *   resolveAllReady()    every ready source, so precheck_graph can present the
 *                        choice that creates the lock.
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

// The registry descriptor for a provider id, or null if unregistered.
function sourceByName(name) {
  return SOURCES.find((source) => source.name === name) || null;
}

/* The session's locked graph record (manifest["graph"]), or null when there is
 * no manifest, no lock, or the manifest cannot be read.
 *
 * Located with findGraphFile so the lock resolves from the same project root
 * every source's detect() resolves graphs against: when --repo points at a
 * subdirectory, a direct lookup would miss the lock and silently fall back to
 * priority order, which is the very substitution this function prevents.
 *
 * Never throws — a bare catch, because JSON.parse throws SyntaxError while the
 * loader throws Error, and both mean "no usable lock". A repo that was never
 * `init`ed still has to work: flow derivation and harvest fall back to registry
 * priority there, so a missing or legacy manifest is an absent lock, not an
 * error. Requiring the manifest loader (not manage_manifest) keeps this
 * cycle-free: manage_manifest requires this registry, never the reverse. */
function readGraphLock(repo) {
  let loadManifest;
  let findGraphFile;
  try {
    ({ loadManifest } = require("../../common/js/_util.js"));
    ({ findGraphFile } = require("./graph_storage.js"));
  } catch {
    return null;
  }
  const found = findGraphFile(repo, [".docforge/manifest.json"]);
  if (!found) return null;
  let manifest;
  try {
    manifest = loadManifest(found);
  } catch {
    return null;
  }
  const lock = manifest && manifest.graph;
  if (!lock || typeof lock !== "object" || !lock.provider) return null;
  return lock;
}

/** The flow capability of one named provider: "native", "derived", or "none".
 *
 * Answers "what can *this* provider offer", never "does any provider have flows" —
 * the repo-wide question recorded flow: "native" for a session locked to CodeGraph
 * merely because an unrelated .ua/domain-graph.json existed. CodeGraph advertises
 * no flow_graph, and references/graph/graph-sources.md is explicit that a selected
 * primary without native flows must read "Docforge-derived (provisional)", never
 * "Native flow source: CodeGraph". */
function flowCapabilityOf(repo, provider) {
  const { DERIVED_FLOW_CANDIDATES, findGraphFile } = require("./graph_storage.js");
  const source = sourceByName(provider);
  if (source && source.capabilities.includes("flow_graph") && source.detect(repo).flow_graph) {
    return "native";
  }
  if (findGraphFile(repo, DERIVED_FLOW_CANDIDATES)) return "derived";
  return "none";
}

/* Resolve `capability` honoring the session's locked provider.
 *
 * The lock is the user's answered choice (see references/graph/graph-sources.md
 * "Session persistence"): once `init` records it, every later step uses that
 * provider instead of re-detecting. Registry priority applies only when no lock
 * exists — otherwise a repo with two graphs would silently analyze the one the
 * user declined.
 *
 * Returns [source, path, origin] where origin is one of:
 *   "lock"            the locked provider supplies `capability`; path is its artifact
 *   "priority"        no lock recorded; fell back to registry order
 *   "lock-stale"      a lock exists but its provider has no artifact on disk;
 *                     source is the locked descriptor, path is null
 *   "lock-uncapable"  the locked provider does not advertise `capability` at all
 *                     (codegraph has no flow_graph, for one); path is null
 *
 * Callers decide what each origin means for them — a stale lock is an error
 * worth stopping for, while "uncapable" is the normal "derive it instead"
 * signal. This never throws and never silently substitutes another provider. */
function resolveLocked(repo, capability) {
  const lock = readGraphLock(repo);
  if (!lock) {
    const [source, found] = resolveFirstReady(repo, capability);
    return [source, found, "priority"];
  }
  const locked = sourceByName(String(lock.provider));
  if (!locked) {
    // The manifest names a provider this registry no longer knows (removed
    // source, or an index written by a newer docforge). Treat it as stale rather
    // than guessing a replacement.
    return [null, null, "lock-stale"];
  }
  if (!locked.capabilities.includes(capability)) return [locked, null, "lock-uncapable"];
  const found = locked.detect(repo)[capability];
  if (!found) return [locked, null, "lock-stale"];
  return [locked, found, "lock"];
}

module.exports = {
  SOURCES,
  sourcesProviding,
  resolveFirstReady,
  resolveAllReady,
  resolveLocked,
  readGraphLock,
  sourceByName,
  flowCapabilityOf,
  setupHintsForMissing,
};
