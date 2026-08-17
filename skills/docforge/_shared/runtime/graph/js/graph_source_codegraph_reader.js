#!/usr/bin/env node
"use strict";
/* CodeGraph offline reader — rank entry points and walk ordered call chains
 * out of .codegraph/codegraph.db.
 *
 * WHY THIS EXISTS. CodeGraph is queried through the `codegraph_explore` MCP
 * tool, which answers semantic questions well but cannot be called from a
 * script. So `derive_flow_graph prepare` used to hand the analyzer a prose
 * paragraph and no data at all, and the agent invented flow skeletons from
 * scratch — file-level narratives with no line numbers and no call order.
 * Meanwhile the db itself holds exactly what a flow skeleton needs: `route`
 * nodes, `references` edges from each route to its handler, and `calls` edges
 * to follow from there.
 *
 * This module reads that structure and nothing else:
 *
 *   - entryPoints(repo)          — ranked seeds (routes, then exported-but-
 *                                  uncalled functions, then call fan-out), in
 *                                  the same shape the understand-anything
 *                                  source returns.
 *   - orderedPaths(repo, seed)   — ordered entry -> terminal chains, each hop
 *                                  carrying file and line.
 *
 * Structure only. Business meaning — actors, branches, rules, failures — still
 * comes from `codegraph_explore` and from reading the source.
 *
 * Access is read-only and guarded on `schema_versions`: an unrecognized schema
 * returns empty rather than guessing, and the caller falls back to the
 * MCP-only path. Never writes — CodeGraph's own watcher owns the db. Requires
 * `node:sqlite` (Node 22.5+ experimental, stable in Node 24); where that is
 * unavailable the Python twin is the offline path.
 *
 * Usage:
 *   node graph_source_codegraph_reader.js entries --repo <path> [--limit 15]
 *   node graph_source_codegraph_reader.js paths --repo <path> --seed <node-id>
 */

const { findGraphFile } = require("./graph_storage.js");
const { PATH_WORDS } = require("../../common/js/entry_vocabulary.js");

const DB_CANDIDATES = [".codegraph/codegraph.db"];

// Highest CodeGraph schema this reader has been checked against. A newer schema
// is not assumed compatible: the reader reports unsupported and the caller
// keeps the MCP-only behaviour rather than reading columns that may have moved.
const MAX_SUPPORTED_SCHEMA = 12;

// Ranking tiers. A route is an entry surface by construction; an exported
// function nobody calls is an entry by elimination; heavy call fan-out is the
// weakest signal and only orders what the first two missed.
const TIER_ROUTE = 1000;
const TIER_EXPORTED_UNCALLED = 600;
const TIER_FANOUT = 300;
const PATH_SIGNAL_BONUS = 150;

const DEFAULT_ENTRY_LIMIT = 15;
const DEFAULT_MAX_DEPTH = 6;
// Per-level successor cap: a hub function with 200 callees must not turn one
// flow into the whole graph.
const DEFAULT_FANOUT_CAP = 6;
// Chains kept per entry point, deepest first. Shorter chains are usually
// prefixes of the deeper ones, so this trims redundancy rather than coverage.
const DEFAULT_MAX_CHAINS = 12;
// Hard ceiling on rows the recursive walk may return, before capping.
const ROW_CAP = 4000;

function findDb(repo) {
  return findGraphFile(repo, DB_CANDIDATES);
}

/** Codepoint ordering, matching Python's `<` on str. `localeCompare` is
 * locale-aware and would order some ids differently from the Python twin. */
function compareIds(a, b) {
  const left = String(a);
  const right = String(b);
  if (left === right) return 0;
  return left < right ? -1 : 1;
}

/** Open the CodeGraph db read-only, or null when it cannot be read safely.
 * Read-only means SQLite will not create -wal/-shm sidecars and cannot write,
 * so this is safe alongside CodeGraph's own watcher process. */
function connect(dbPath) {
  let sqlite;
  try {
    sqlite = require("node:sqlite");
  } catch {
    return null; // Node too old — the Python twin is the offline path.
  }
  let db;
  try {
    db = new sqlite.DatabaseSync(String(dbPath), { readOnly: true });
  } catch {
    return null;
  }
  try {
    const row = db.prepare("SELECT max(version) AS version FROM schema_versions").get();
    const version = row ? row.version : null;
    if (!Number.isInteger(version) || version > MAX_SUPPORTED_SCHEMA) {
      // Newer than we know: let the caller fall back to codegraph_explore
      // instead of reading columns that may have been renamed.
      db.close();
      return null;
    }
  } catch {
    db.close();
    return null;
  }
  return db;
}

function makeSeed(row, tier, fanout) {
  const pathValue = row.file_path;
  const bonus = pathValue && PATH_WORDS.test(String(pathValue)) ? PATH_SIGNAL_BONUS : 0;
  return {
    id: row.id,
    name: row.name,
    kind: row.kind,
    path: pathValue,
    line: row.start_line,
    rank: tier + bonus + fanout,
  };
}

/** Ranked flow-derivation seeds, highest rank first. Returns [] when there is
 * no readable db, which is what makes this safe to hang off the SOURCE
 * descriptor: derive_flow_graph already treats an empty seed list as "no
 * entry-point signal" and falls back. */
function entryPoints(repo, limit) {
  const dbPath = findDb(repo);
  if (!dbPath) return [];
  const db = connect(dbPath);
  if (!db) return [];
  const seeds = [];
  try {
    const fanout = new Map();
    for (const row of db.prepare(
      "SELECT source, count(*) AS n FROM edges WHERE kind = 'calls' GROUP BY source"
    ).all()) {
      fanout.set(row.source, row.n);
    }
    const seen = new Set();

    // A route node has no outgoing `calls` of its own, so its own fan-out is
    // always 0 and every route would tie — leaving "which 15 flows matter"
    // decided alphabetically. Score a route by what its handler reaches.
    const handlerReach = new Map();
    for (const row of db.prepare(
      "SELECT r.id AS route, count(*) AS n " +
      "  FROM nodes r " +
      "  JOIN edges h ON h.source = r.id AND h.kind IN ('references', 'calls') " +
      "  JOIN edges c ON c.source = h.target " +
      " WHERE r.kind = 'route' GROUP BY r.id"
    ).all()) {
      handlerReach.set(row.route, row.n);
    }
    for (const row of db.prepare(
      "SELECT id, name, kind, file_path, start_line FROM nodes WHERE kind = 'route' ORDER BY qualified_name"
    ).all()) {
      seeds.push(makeSeed(row, TIER_ROUTE, handlerReach.get(row.id) || 0));
      seen.add(row.id);
    }

    for (const row of db.prepare(
      "SELECT n.id, n.name, n.kind, n.file_path, n.start_line FROM nodes n " +
      "WHERE n.kind IN ('function', 'method') AND n.is_exported = 1 " +
      "  AND NOT EXISTS (SELECT 1 FROM edges e WHERE e.target = n.id AND e.kind = 'calls') " +
      "ORDER BY n.qualified_name"
    ).all()) {
      if (seen.has(row.id)) continue;
      seeds.push(makeSeed(row, TIER_EXPORTED_UNCALLED, fanout.get(row.id) || 0));
      seen.add(row.id);
    }

    for (const row of db.prepare(
      "SELECT n.id, n.name, n.kind, n.file_path, n.start_line FROM nodes n " +
      "WHERE n.kind IN ('function', 'method') ORDER BY n.qualified_name"
    ).all()) {
      if (seen.has(row.id) || (fanout.get(row.id) || 0) < 3) continue;
      seeds.push(makeSeed(row, TIER_FANOUT, fanout.get(row.id)));
      seen.add(row.id);
    }
  } catch {
    return [];
  } finally {
    db.close();
  }

  // Rank desc, then id asc — a total order, so the Python twin agrees.
  seeds.sort((a, b) => (b.rank - a.rank) || compareIds(a.id, b.id));
  return limit ? seeds.slice(0, limit) : seeds;
}

/** The trail one hop shorter; "" for a first hop. */
function parentTrail(trail) {
  const parts = trail.split(">").filter(Boolean);
  return parts.length > 1 ? `>${parts.slice(0, -1).join(">")}>` : "";
}

/** Ordered call chains leaving one entry point, deepest-first.
 *
 * Both `references` and `calls` are followed at every depth. `references` is
 * not optional decoration here: a route reaches its handler through it, and in
 * a JS codebase a handler reaches its service object through it too (the
 * service is a `constant` node). The generic edge-hint filter excluded
 * `references` entirely, which broke every route chain at hop 0. Including it
 * at all depths costs about 2.3x the rows on a real repo — cheap for the hop
 * it buys.
 *
 * Cycles are cut on the accumulated trail, which matters more than it looks:
 * self-recursive handlers are common, and without the guard a single self-edge
 * walks to the depth limit and reports a chain that does not exist. */
function orderedPaths(repo, seedId, maxDepth = DEFAULT_MAX_DEPTH, fanoutCap = DEFAULT_FANOUT_CAP, maxChains = DEFAULT_MAX_CHAINS) {
  const dbPath = findDb(repo);
  if (!dbPath) return [];
  const db = connect(dbPath);
  if (!db) return [];
  let rows;
  try {
    rows = db.prepare(`
      WITH RECURSIVE walk(node, depth, trail) AS (
        SELECT e.target, 1, '>' || e.target || '>'
          FROM edges e
         WHERE e.source = ? AND e.kind IN ('references', 'calls')
        UNION ALL
        SELECT e.target, w.depth + 1, w.trail || e.target || '>'
          FROM walk w JOIN edges e ON e.source = w.node
         WHERE e.kind IN ('references', 'calls')
           AND w.depth < ?
           AND instr(w.trail, '>' || e.target || '>') = 0
      )
      SELECT w.depth, w.trail, n.id, n.name, n.qualified_name,
             n.kind, n.file_path, n.start_line
        FROM walk w JOIN nodes n ON n.id = w.node
       ORDER BY w.depth, n.qualified_name
       LIMIT ?
    `).all(seedId, maxDepth, ROW_CAP);
  } catch {
    return [];
  } finally {
    db.close();
  }

  const byTrail = new Map();
  const children = new Map();
  for (const row of rows) {
    byTrail.set(row.trail, {
      order: row.depth,
      nodeId: row.id,
      symbol: row.name,
      file: row.file_path,
      line: row.start_line,
      kind: row.kind,
    });
    const parent = parentTrail(row.trail);
    if (!children.has(parent)) children.set(parent, []);
    children.get(parent).push(row.trail);
  }

  // How far each branch still goes, computed deepest-first. Needed before
  // capping: truncating a fan-out alphabetically amputates whichever branch
  // happens to sort late, which on a real repo silently cut six-hop flows
  // down to three.
  const reach = new Map();
  const deepestFirst = [...byTrail.keys()].sort((a, b) => byTrail.get(b).order - byTrail.get(a).order);
  for (const trail of deepestFirst) {
    let best = 0;
    for (const child of children.get(trail) || []) best = Math.max(best, reach.get(child) || 0);
    reach.set(trail, 1 + best);
  }

  // Cap successors per node, keeping the branches that lead furthest and
  // breaking ties on node id so both runtimes agree.
  for (const [parent, trails] of children.entries()) {
    trails.sort((a, b) =>
      ((reach.get(b) || 0) - (reach.get(a) || 0))
      || compareIds(byTrail.get(a).nodeId, byTrail.get(b).nodeId));
    children.set(parent, trails.slice(0, fanoutCap));
  }

  const kept = new Set();
  const frontier = [...(children.get("") || [])];
  while (frontier.length) {
    const trail = frontier.pop();
    if (kept.has(trail)) continue;
    kept.add(trail);
    frontier.push(...(children.get(trail) || []));
  }

  const chains = [];
  for (const trail of kept) {
    if ((children.get(trail) || []).some((child) => kept.has(child))) continue; // not terminal
    const chain = [];
    let cursor = trail;
    while (cursor) {
      chain.push(byTrail.get(cursor));
      cursor = parentTrail(cursor);
    }
    chains.push(chain.reverse());
  }
  // Deepest first, then the full node sequence — comparing only the endpoints
  // is not a total order (two 4-hop chains can share both ends), and a
  // non-total order makes the two runtimes disagree.
  const sequence = (chain) => chain.map((hop) => String(hop.nodeId));
  chains.sort((a, b) => {
    if (a.length !== b.length) return b.length - a.length;
    const left = sequence(a);
    const right = sequence(b);
    for (let i = 0; i < left.length; i++) {
      if (left[i] !== right[i]) return left[i] < right[i] ? -1 : 1;
    }
    return 0;
  });
  // One entry point can terminate in dozens of leaves (93 on a real repo), and
  // the deepest chains already cover the shallow ones as prefixes. Cap so a
  // single fan-heavy handler cannot dominate the analyzer's context.
  return chains.slice(0, maxChains);
}

function parseArgs(argv) {
  const args = { command: argv[0], limit: DEFAULT_ENTRY_LIMIT, maxDepth: DEFAULT_MAX_DEPTH, fanoutCap: DEFAULT_FANOUT_CAP, maxChains: DEFAULT_MAX_CHAINS };
  for (let i = 1; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--repo") args.repo = argv[++i];
    else if (a === "--seed") args.seed = argv[++i];
    else if (a === "--limit") args.limit = parseInt(argv[++i], 10);
    else if (a === "--max-depth") args.maxDepth = parseInt(argv[++i], 10);
    else if (a === "--fanout-cap") args.fanoutCap = parseInt(argv[++i], 10);
    else if (a === "--max-chains") args.maxChains = parseInt(argv[++i], 10);
  }
  return args;
}

function main() {
  const args = parseArgs(process.argv.slice(2));
  if (!args.repo || !["entries", "paths"].includes(args.command)) {
    console.error("usage: graph_source_codegraph_reader.js entries --repo <path> [--limit <n>]");
    console.error("       graph_source_codegraph_reader.js paths --repo <path> --seed <node-id> [--max-depth <n>]");
    return 2;
  }
  if (args.command === "entries") {
    const seeds = entryPoints(args.repo, args.limit);
    if (!seeds.length) {
      console.error("No CodeGraph entry points readable — no .codegraph/codegraph.db, an "
        + "unsupported schema, or no node:sqlite. Query codegraph_explore instead "
        + "(references/graph/graph-source-codegraph.md).");
      return 1;
    }
    console.log(JSON.stringify(seeds, null, 2));
    return 0;
  }
  if (!args.seed) {
    console.error("paths needs --seed <node-id>");
    return 2;
  }
  const chains = orderedPaths(args.repo, args.seed, args.maxDepth, args.fanoutCap, args.maxChains);
  if (!chains.length) {
    console.error(`No outgoing call chains from ${args.seed}.`);
    return 1;
  }
  console.log(JSON.stringify(chains, null, 2));
  return 0;
}

module.exports = { entryPoints, orderedPaths, main, MAX_SUPPORTED_SCHEMA };

if (require.main === module) process.exit(main());
