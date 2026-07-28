#!/usr/bin/env python3
"""GitNexus graph source: index detection, plus building docforge's
.ua/knowledge-graph.json and .ua/domain-graph.json from a GitNexus index.

GitNexus (https://github.com/abhigyanpatwari/GitNexus) stores its own graph
in an opaque embedded database (.gitnexus/lbug) reachable only through MCP
tools (`cypher`, resource reads) — there is no file this script can read
directly, and no MCP client available to a plain script. So the contract
here is agent-mediated: the acting agent runs the three fixed Cypher queries
documented in references/gitnexus-bridge.md (fixed RETURN aliases — this
script does not guess column names), saves each raw result to a JSON file,
then invokes:

    python graph_source_gitnexus.py build --repo <path> \\
        --nodes nodes.json --edges edges.json --processes processes.json

`detect(repo)` only checks whether a GitNexus index exists at all
(.gitnexus/meta.json) — it says nothing about whether .ua/*.json has been
built from it yet; that's what check_preconditions.py's orchestration is for.

Usage:
    python graph_source_gitnexus.py detect --repo <path>
    python graph_source_gitnexus.py build --repo <path> --nodes <f> --edges <f> --processes <f>
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from graph_common import find, write_graph

SOURCE_NAME = "gitnexus"

INDEX_MARKER_CANDIDATES = [".gitnexus/meta.json"]

# Fixed RETURN aliases the bridge doc's Cypher queries must use. Kept as a
# single source of truth so the doc and this script cannot silently drift.
NODE_COLUMNS = ("id", "name", "path", "type")
EDGE_COLUMNS = ("source", "target", "type")
PROCESS_COLUMNS = ("processName", "stepIndex", "symbolId", "symbolName", "path")


def detect(repo: Path) -> dict:
    """Look for a GitNexus index. Returns {"index": Path|None}."""
    return {"index": find(repo, INDEX_MARKER_CANDIDATES)}


def normalize_rows(raw) -> list[dict]:
    """Accept either shape a Cypher-query JSON dump might arrive in:
    a plain array of row-objects (most MCP tool results), or a
    {"columns": [...], "rows": [[...], ...]} envelope (common driver output).
    Always returns a list of plain dicts keyed by the RETURN aliases."""
    if isinstance(raw, list):
        return raw
    if isinstance(raw, dict) and "rows" in raw and "columns" in raw:
        cols = raw["columns"]
        return [dict(zip(cols, row)) for row in raw["rows"]]
    raise ValueError(
        "unrecognized Cypher result shape — expected a JSON array of row "
        "objects, or {\"columns\": [...], \"rows\": [[...], ...]}"
    )


def require_columns(rows: list[dict], columns: tuple[str, ...], label: str) -> None:
    if not rows:
        return
    missing = [c for c in columns if c not in rows[0]]
    if missing:
        raise ValueError(
            f"{label} rows are missing expected column(s) {missing} — "
            f"the Cypher query must RETURN exactly {list(columns)} "
            "(see references/gitnexus-bridge.md)"
        )


def build_knowledge_graph(node_rows: list[dict], edge_rows: list[dict]) -> dict:
    require_columns(node_rows, NODE_COLUMNS, "node")
    require_columns(edge_rows, EDGE_COLUMNS, "edge")
    nodes = [
        {"id": r["id"], "name": r["name"], "path": r["path"], "type": r["type"]}
        for r in node_rows
    ]
    edges = [
        {"source": r["source"], "target": r["target"], "type": r["type"]}
        for r in edge_rows
    ]
    return {"nodes": nodes, "edges": edges, "source": SOURCE_NAME}


def build_domain_graph(process_rows: list[dict]) -> dict:
    """Group STEP_IN_PROCESS rows into one flow per process, steps ordered by
    stepIndex. GitNexus's Community clusters are not mapped to domains in
    this first pass — there is no reliable cluster-to-process linkage
    available without a fourth query, so flows are reported flat rather than
    invented under an ungrounded domain grouping."""
    require_columns(process_rows, PROCESS_COLUMNS, "process")
    flows_by_name: dict[str, list[dict]] = {}
    for r in process_rows:
        flows_by_name.setdefault(r["processName"], []).append(r)

    flows = []
    for name, rows in flows_by_name.items():
        rows.sort(key=lambda r: r["stepIndex"])
        flows.append({
            "name": name,
            "steps": [
                {
                    "order": r["stepIndex"],
                    "symbolId": r["symbolId"],
                    "symbolName": r["symbolName"],
                    "path": r["path"],
                }
                for r in rows
            ],
        })
    return {"flows": flows, "source": SOURCE_NAME}


def load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise ValueError(f"file not found: {path}")
    except json.JSONDecodeError as e:
        raise ValueError(f"invalid JSON in {path}: {e}")


def cmd_detect(args: argparse.Namespace) -> int:
    result = detect(args.repo)
    if result["index"]:
        print(f"READY  gitnexus index  -> {result['index']}")
        return 0
    print("MISSING  gitnexus index  (checked for .gitnexus/meta.json)")
    print("  Fix: from the repo root, run:")
    print("    npx gitnexus analyze")
    print("    npx gitnexus setup")
    print("  Then re-run this check.")
    return 1


def cmd_build(args: argparse.Namespace) -> int:
    try:
        node_rows = normalize_rows(load_json(args.nodes))
        edge_rows = normalize_rows(load_json(args.edges))
        process_rows = normalize_rows(load_json(args.processes))
        knowledge_graph = build_knowledge_graph(node_rows, edge_rows)
        domain_graph = build_domain_graph(process_rows)
        kg_path, dg_path = write_graph(args.repo, knowledge_graph, domain_graph)
    except ValueError as e:
        print(f"BUILD FAILED: {e}", file=sys.stderr)
        return 1

    print(f"Wrote {kg_path} ({len(knowledge_graph['nodes'])} nodes, "
          f"{len(knowledge_graph['edges'])} edges)")
    print(f"Wrote {dg_path} ({len(domain_graph['flows'])} flows)")
    print("Re-run check_preconditions.py --need domain to confirm READY.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="command", required=True)

    p_detect = sub.add_parser("detect", help="check whether a GitNexus index exists")
    p_detect.add_argument("--repo", required=True, type=Path)
    p_detect.set_defaults(func=cmd_detect)

    p_build = sub.add_parser("build", help="build .ua/*.json from raw Cypher dumps")
    p_build.add_argument("--repo", required=True, type=Path)
    p_build.add_argument("--nodes", required=True, type=Path)
    p_build.add_argument("--edges", required=True, type=Path)
    p_build.add_argument("--processes", required=True, type=Path)
    p_build.set_defaults(func=cmd_build)

    args = ap.parse_args()
    if not args.repo.is_dir():
        print(f"Not a directory: {args.repo}", file=sys.stderr)
        return 2
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
