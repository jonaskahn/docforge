#!/usr/bin/env python3
"""GitNexus offline reader — inventory the ladybug DB (.gitnexus/lbug) directly.

USE THIS ONLY for the GitNexus source, and only when the gitnexus MCP is not
wired into this session. When the MCP is available it is the better read path
(richer, no dependency); this script exists for offline/scripted reads. On most
machines the Node twin (graph_source_gitnexus_reader.js, backed by the published
@ladybugdb/core native module) is the reliable offline path — this Python twin
works only where a ladybug Python binding is installed.

It opens .gitnexus/lbug read-only and prints the same kind of inventory
read_graph.py gives for a JSON graph — module map, functional areas, flows,
most-imported targets — to seed a documentation set. Output is an inventory to
verify, not finished prose.

The ladybug binding is an optional dependency and the single documented
exception to docforge's "no install" rule. If it is not importable this script
prints how to proceed (use the MCP, or the Node reader) and exits non-zero — it
never crashes with a raw traceback.

Usage:
    python graph_source_gitnexus_reader.py --repo <path> --summary
    python graph_source_gitnexus_reader.py --repo <path> --modules --flows
    python graph_source_gitnexus_reader.py --db <path/to/lbug> --layers
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .graph_storage import find_graph_file

HINT = [
    "Could not read the ladybug DB offline. Either:",
    "  - read it via the gitnexus MCP (cypher/query/context) — the preferred path; or",
    "  - use the Node reader (graph_source_gitnexus_reader.js) with @ladybugdb/core; or",
    "  - install a ladybug Python binding.",
    "See references/graph/graph-source-gitnexus.md.",
]

# Node labels docforge cares about, for the SHAPE summary.
SUMMARY_LABELS = ["File", "Function", "Method", "Class", "Interface",
                  "Community", "Process", "Route", "Tool"]


def abort_lines(lines: list[str]) -> int:
    for line in lines:
        print(line, file=sys.stderr)
    return 1


def load_binding():
    """Return an imported ladybug graph-DB module exposing Database/Connection,
    or None. Deliberately does NOT try the unrelated PyPI package named
    'ladybug' (a building-energy library)."""
    for name in ("ladybugdb", "lbug"):
        try:
            module = __import__(name)
        except ImportError:
            continue
        if hasattr(module, "Database") and hasattr(module, "Connection"):
            return module
    return None


def open_connection(module, db_path: Path):
    """Open a read-only connection. Try the read-only keyword first, fall back
    to positional forms, since binding signatures vary."""
    for make_db in (
        lambda: module.Database(str(db_path), read_only=True),
        lambda: module.Database(str(db_path)),
    ):
        try:
            database = make_db()
            return module.Connection(database)
        except TypeError:
            continue
    # Last attempt surfaces the real error to the caller.
    database = module.Database(str(db_path))
    return module.Connection(database)


def make_query(connection):
    """Return a query(cypher) -> list[dict] helper over the binding's result
    object (Kùzu-compatible: execute() + column names + row iteration)."""
    def query(cypher: str):
        try:
            result = connection.execute(cypher)
            columns = result.get_column_names()
            rows = []
            while result.has_next():
                values = result.get_next()
                rows.append(dict(zip(columns, values)))
            return rows
        except Exception as error:  # noqa: BLE001 — surface as empty + note
            return {"__error": str(error)}
    return query


def rows_or(result):
    return result if isinstance(result, list) else []


def print_summary(query) -> None:
    print("SHAPE")
    total = rows_or(query("MATCH (n) RETURN count(n) AS c"))
    print(f"  nodes total    : {total[0]['c'] if total else '?'}")
    for label in SUMMARY_LABELS:
        rows = rows_or(query(f"MATCH (n:{label}) RETURN count(n) AS c"))
        if rows and rows[0].get("c"):
            print(f"  {label:<14}: {rows[0]['c']}")
    print()


def print_modules(query, limit: int) -> None:
    files = rows_or(query("MATCH (f:File) RETURN f.filePath AS path"))
    counts: dict[str, int] = {}
    for row in files:
        path = row.get("path")
        if not path:
            continue
        directory = "/".join(str(path).split("/")[:-1]) or "."
        counts[directory] = counts.get(directory, 0) + 1
    print(f"MODULES ({len(counts)})")
    for directory, count in sorted(counts.items(), key=lambda kv: -kv[1])[:limit]:
        print(f"  {directory}/  [{count} files]")
    if len(counts) > limit:
        print(f"  ... {len(counts) - limit} more (raise --limit)")
    print("\n  Seeds docs/architecture/high-level.md. Confirm each module's purpose")
    print("  with the gitnexus MCP `context`/`query` before describing it.\n")


def print_layers(query, limit: int) -> None:
    areas = rows_or(query(
        "MATCH (f)-[:CodeRelation {type:'MEMBER_OF'}]->(c:Community) "
        "RETURN c.heuristicLabel AS area, count(f) AS n ORDER BY n DESC"))
    if not areas:
        print("FUNCTIONAL AREAS\n  No Community membership found.\n")
        return
    print(f"FUNCTIONAL AREAS ({len(areas)}) — GitNexus Community clusters")
    for row in areas[:limit]:
        print(f"  {str(row.get('area') or '(unnamed)'):<28} {row.get('n')} members")
    print()


def print_flows(query, limit: int) -> None:
    flows = rows_or(query(
        "MATCH (s)-[r:CodeRelation {type:'STEP_IN_PROCESS'}]->(p:Process) "
        "RETURN p.heuristicLabel AS name, count(r) AS steps ORDER BY steps DESC"))
    if not flows:
        print("FLOWS\n  No Process/STEP_IN_PROCESS data found.\n")
        return
    print(f"FLOWS ({len(flows)}) — GitNexus Process execution traces")
    for row in flows[:limit]:
        print(f"  {str(row.get('name') or '(unnamed)')}  [{row.get('steps')} steps]")
    if len(flows) > limit:
        print(f"  ... {len(flows) - limit} more (raise --limit)")
    print("\n  These are code-derived Entry → Terminal candidates, not one document each.")
    print("  Group them by entryPointId in the flow index, then document only ranked main")
    print("  entries whose behavior is confirmed (references/graph/flow-derivation.md).\n")


def print_deps(query, limit: int) -> None:
    imports = rows_or(query(
        "MATCH ()-[r:CodeRelation {type:'IMPORTS'}]->(b) "
        "RETURN b.name AS name, count(r) AS n ORDER BY n DESC"))
    if not imports:
        print("IMPORTS\n  No IMPORTS edges found.\n")
        return
    print(f"MOST-IMPORTED TARGETS ({len(imports)})")
    for row in imports[:limit]:
        print(f"  {str(row.get('name') or '(unnamed)'):<40} {row.get('n')} import(s)")
    print("\n  Candidates for docs/architecture/dependencies.md. Versions and licences")
    print("  come from the manifest/lockfile, not the graph.\n")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", type=Path)
    ap.add_argument("--db", type=Path, help="explicit path to the lbug DB")
    ap.add_argument("--limit", type=int, default=40)
    ap.add_argument("--summary", action="store_true")
    ap.add_argument("--modules", action="store_true")
    ap.add_argument("--layers", action="store_true")
    ap.add_argument("--flows", action="store_true")
    ap.add_argument("--deps", action="store_true")
    args = ap.parse_args()

    db_path = args.db
    if not db_path:
        if not args.repo:
            return abort_lines(["--repo <path> or --db <path/to/lbug> is required"])
        db_path = find_graph_file(args.repo, [".gitnexus/lbug"])
        if not db_path:
            return abort_lines([
                f"No .gitnexus/lbug found from {args.repo} up to the git root.",
                "Build a GitNexus index first: npx gitnexus analyze "
                "(see references/graph/graph-source-gitnexus.md).",
            ])

    module = load_binding()
    if module is None:
        return abort_lines(HINT)

    try:
        connection = open_connection(module, db_path)
    except Exception as error:  # noqa: BLE001
        return abort_lines([f"Failed to open {db_path}: {error}", "", *HINT])

    query = make_query(connection)

    want_all = args.summary or not any((args.modules, args.layers, args.flows, args.deps))

    print(f"# {db_path}  (ladybug DB)\n")
    if args.summary or want_all:
        print_summary(query)
    if args.modules or want_all:
        print_modules(query, args.limit)
    if args.layers or want_all:
        print_layers(query, args.limit)
    if args.flows or want_all:
        print_flows(query, args.limit)
    if args.deps or want_all:
        print_deps(query, args.limit)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
