#!/usr/bin/env python3
"""CodeGraph offline reader — rank entry points and walk ordered call chains
out of .codegraph/codegraph.db.

WHY THIS EXISTS. CodeGraph is queried through the `codegraph_explore` MCP tool,
which answers semantic questions well but cannot be called from a script. So
`derive_flow_graph prepare` used to hand the analyzer a prose paragraph and no
data at all, and the agent invented flow skeletons from scratch — file-level
narratives with no line numbers and no call order. Meanwhile the db itself
holds exactly what a flow skeleton needs: `route` nodes, `references` edges
from each route to its handler, and `calls` edges to follow from there.

This module reads that structure and nothing else:

  * `entry_points(repo)` — ranked seeds (routes, then exported-but-uncalled
    functions, then call fan-out), in the same shape the understand-anything
    source returns, so derive_flow_graph consumes them unchanged.
  * `ordered_paths(repo, seed_id, ...)` — ordered entry -> terminal chains,
    each hop carrying file and line.

**Structure only.** Business meaning — actors, branches, rules, failures —
still comes from `codegraph_explore` and from reading the source. The division
is deliberate: SQL is good at "what calls what, in what order", and bad at
"what does this mean".

Access is read-only (`file:...?mode=ro`) and guarded on `schema_versions`: an
unrecognized schema returns empty rather than guessing, and the caller falls
back to the MCP-only path. Never writes — CodeGraph's own watcher owns the db.

Usage:
    python graph_source_codegraph_reader.py entries --repo <path> [--limit 15]
    python graph_source_codegraph_reader.py paths --repo <path> --seed <node-id>
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

from .graph_storage import find_graph_file
from ...common.python.entry_vocabulary import PATH_WORDS

DB_CANDIDATES = [".codegraph/codegraph.db"]

# Highest CodeGraph schema this reader has been checked against. A newer schema
# is not assumed compatible: the reader reports unsupported and the caller
# keeps the MCP-only behaviour rather than reading columns that may have moved.
MAX_SUPPORTED_SCHEMA = 12

# Ranking tiers. A route is an entry surface by construction; an exported
# function nobody calls is an entry by elimination; heavy call fan-out is the
# weakest signal and only orders what the first two missed.
TIER_ROUTE = 1000
TIER_EXPORTED_UNCALLED = 600
TIER_FANOUT = 300
PATH_SIGNAL_BONUS = 150

DEFAULT_ENTRY_LIMIT = 15
DEFAULT_MAX_DEPTH = 6
# Per-level successor cap: a hub function with 200 callees must not turn one
# flow into the whole graph.
DEFAULT_FANOUT_CAP = 6
# Chains kept per entry point, deepest first. Shorter chains are usually
# prefixes of the deeper ones, so this trims redundancy rather than coverage.
DEFAULT_MAX_CHAINS = 12
# Hard ceiling on rows the recursive walk may return, before capping.
ROW_CAP = 4000


def find_db(repo: Path) -> Path | None:
    return find_graph_file(repo, DB_CANDIDATES)


def connect(db_path: Path) -> sqlite3.Connection | None:
    """Open the CodeGraph db read-only, or None when it cannot be read safely.

    `mode=ro` means SQLite will not create -wal/-shm sidecars and cannot write,
    so this is safe alongside CodeGraph's own watcher process."""
    try:
        connection = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    except sqlite3.Error:
        return None
    connection.row_factory = sqlite3.Row
    try:
        row = connection.execute("SELECT max(version) AS version FROM schema_versions").fetchone()
    except sqlite3.Error:
        connection.close()
        return None
    version = row["version"] if row else None
    if not isinstance(version, int) or version > MAX_SUPPORTED_SCHEMA:
        # Newer than we know: let the caller fall back to codegraph_explore
        # instead of reading columns that may have been renamed.
        connection.close()
        return None
    return connection


def _seed(row: sqlite3.Row, tier: int, fanout: int) -> dict:
    path_value = row["file_path"]
    bonus = PATH_SIGNAL_BONUS if path_value and PATH_WORDS.search(str(path_value)) else 0
    return {
        "id": row["id"],
        "name": row["name"],
        "kind": row["kind"],
        "path": path_value,
        "line": row["start_line"],
        "rank": tier + bonus + fanout,
    }


def entry_points(repo: Path, limit: int | None = None) -> list[dict]:
    """Ranked flow-derivation seeds, highest rank first.

    Returns [] when there is no readable db, which is what makes this safe to
    hang off the SOURCE descriptor: derive_flow_graph already treats an empty
    seed list as "no entry-point signal" and falls back."""
    db_path = find_db(repo)
    if not db_path:
        return []
    connection = connect(db_path)
    if connection is None:
        return []
    try:
        fanout = {
            row["source"]: row["n"]
            for row in connection.execute(
                "SELECT source, count(*) AS n FROM edges WHERE kind = 'calls' GROUP BY source"
            )
        }
        seeds: list[dict] = []
        seen: set = set()

        # A route node has no outgoing `calls` of its own, so its own fan-out
        # is always 0 and every route would tie — leaving "which 15 flows
        # matter" decided alphabetically. Score a route by what its handler
        # reaches instead.
        handler_reach = {
            row["route"]: row["n"]
            for row in connection.execute(
                "SELECT r.id AS route, count(*) AS n "
                "  FROM nodes r "
                "  JOIN edges h ON h.source = r.id AND h.kind IN ('references', 'calls') "
                "  JOIN edges c ON c.source = h.target "
                " WHERE r.kind = 'route' GROUP BY r.id"
            )
        }
        for row in connection.execute(
            "SELECT id, name, kind, file_path, start_line FROM nodes "
            "WHERE kind = 'route' ORDER BY qualified_name"
        ):
            seeds.append(_seed(row, TIER_ROUTE, handler_reach.get(row["id"], 0)))
            seen.add(row["id"])

        for row in connection.execute(
            "SELECT n.id, n.name, n.kind, n.file_path, n.start_line FROM nodes n "
            "WHERE n.kind IN ('function', 'method') AND n.is_exported = 1 "
            "  AND NOT EXISTS (SELECT 1 FROM edges e WHERE e.target = n.id AND e.kind = 'calls') "
            "ORDER BY n.qualified_name"
        ):
            if row["id"] in seen:
                continue
            seeds.append(_seed(row, TIER_EXPORTED_UNCALLED, fanout.get(row["id"], 0)))
            seen.add(row["id"])

        for row in connection.execute(
            "SELECT n.id, n.name, n.kind, n.file_path, n.start_line FROM nodes n "
            "WHERE n.kind IN ('function', 'method') ORDER BY n.qualified_name"
        ):
            if row["id"] in seen or fanout.get(row["id"], 0) < 3:
                continue
            seeds.append(_seed(row, TIER_FANOUT, fanout[row["id"]]))
            seen.add(row["id"])
    except sqlite3.Error:
        return []
    finally:
        connection.close()

    # Rank desc, then id asc — a total order, so the Node twin agrees.
    seeds.sort(key=lambda seed: (-seed["rank"], str(seed["id"])))
    return seeds[:limit] if limit else seeds


def ordered_paths(
    repo: Path,
    seed_id: str,
    max_depth: int = DEFAULT_MAX_DEPTH,
    fanout_cap: int = DEFAULT_FANOUT_CAP,
    max_chains: int = DEFAULT_MAX_CHAINS,
) -> list[list[dict]]:
    """Ordered call chains leaving one entry point, deepest-first.

    Both `references` and `calls` are followed at every depth. `references` is
    not optional decoration here: a route reaches its handler through it, and
    in a JS codebase a handler reaches its service object through it too
    (the service is a `constant` node). The generic edge-hint filter excluded
    `references` entirely, which broke every route chain at hop 0. Including it
    at all depths costs about 2.3x the rows on a real repo — cheap for the hop
    it buys.

    Cycles are cut on the accumulated trail, which matters more than it looks:
    self-recursive handlers are common, and without the guard a single
    self-edge walks to the depth limit and reports a chain that does not
    exist."""
    db_path = find_db(repo)
    if not db_path:
        return []
    connection = connect(db_path)
    if connection is None:
        return []
    try:
        rows = connection.execute(
            """
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
            """,
            (seed_id, max_depth, ROW_CAP),
        ).fetchall()
    except sqlite3.Error:
        return []
    finally:
        connection.close()

    by_trail: dict[str, dict] = {}
    children: dict[str, list[str]] = {}
    for row in rows:
        trail = row["trail"]
        by_trail[trail] = {
            "order": row["depth"],
            "nodeId": row["id"],
            "symbol": row["name"],
            "file": row["file_path"],
            "line": row["start_line"],
            "kind": row["kind"],
        }
        parent = _parent_trail(trail)
        children.setdefault(parent, []).append(trail)

    # How far each branch still goes, computed deepest-first. Needed before
    # capping: truncating a fan-out alphabetically amputates whichever branch
    # happens to sort late, which on a real repo silently cut six-hop flows
    # down to three.
    reach: dict[str, int] = {}
    for trail in sorted(by_trail, key=lambda value: -by_trail[value]["order"]):
        reach[trail] = 1 + max((reach.get(child, 0) for child in children.get(trail, ())), default=0)

    # Cap successors per node, keeping the branches that lead furthest and
    # breaking ties on node id so both runtimes agree.
    for parent, trails in children.items():
        trails.sort(key=lambda value: (-reach.get(value, 0), str(by_trail[value]["nodeId"])))
        del trails[fanout_cap:]

    kept: set = set()
    frontier = list(children.get("", ()))
    while frontier:
        trail = frontier.pop()
        if trail in kept:
            continue
        kept.add(trail)
        frontier.extend(children.get(trail, ()))

    chains: list[list[dict]] = []
    for trail in kept:
        if any(child in kept for child in children.get(trail, ())):
            continue  # not a terminal hop
        chain = []
        cursor = trail
        while cursor:
            chain.append(by_trail[cursor])
            cursor = _parent_trail(cursor)
        chains.append(list(reversed(chain)))
    # Deepest first, then the full node sequence — comparing only the endpoints
    # is not a total order (two 4-hop chains can share both ends), and a
    # non-total order makes the two runtimes disagree.
    chains.sort(key=lambda chain: (-len(chain), [str(hop["nodeId"]) for hop in chain]))
    # One entry point can terminate in dozens of leaves (93 on a real repo),
    # and the deepest chains already cover the shallow ones as prefixes. Cap so
    # a single fan-heavy handler cannot dominate the analyzer's context.
    return chains[:max_chains]


def _parent_trail(trail: str) -> str:
    """The trail one hop shorter; '' for a first hop."""
    parts = [part for part in trail.split(">") if part]
    return ">" + ">".join(parts[:-1]) + ">" if len(parts) > 1 else ""


def run_entries(args: argparse.Namespace) -> int:
    seeds = entry_points(args.repo, args.limit)
    if not seeds:
        print("No CodeGraph entry points readable — no .codegraph/codegraph.db, or an "
              "unsupported schema. Query codegraph_explore instead "
              "(references/graph/graph-source-codegraph.md).", file=sys.stderr)
        return 1
    print(json.dumps(seeds, indent=2))
    return 0


def run_paths(args: argparse.Namespace) -> int:
    chains = ordered_paths(args.repo, args.seed, args.max_depth, args.fanout_cap, args.max_chains)
    if not chains:
        print(f"No outgoing call chains from {args.seed}.", file=sys.stderr)
        return 1
    print(json.dumps(chains, indent=2))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="command", required=True)

    p_entries = sub.add_parser("entries", help="ranked entry-point seeds as JSON")
    p_entries.add_argument("--repo", required=True, type=Path)
    p_entries.add_argument("--limit", type=int, default=DEFAULT_ENTRY_LIMIT)
    p_entries.set_defaults(func=run_entries)

    p_paths = sub.add_parser("paths", help="ordered call chains from one seed as JSON")
    p_paths.add_argument("--repo", required=True, type=Path)
    p_paths.add_argument("--seed", required=True)
    p_paths.add_argument("--max-depth", type=int, default=DEFAULT_MAX_DEPTH)
    p_paths.add_argument("--fanout-cap", type=int, default=DEFAULT_FANOUT_CAP)
    p_paths.add_argument("--max-chains", type=int, default=DEFAULT_MAX_CHAINS)
    p_paths.set_defaults(func=run_paths)

    args = ap.parse_args()
    if not args.repo.is_dir():
        print(f"Not a directory: {args.repo}", file=sys.stderr)
        return 2
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
