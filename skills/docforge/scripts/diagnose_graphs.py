#!/usr/bin/env python3
"""Validate and report on graph files at repository root.

Helps diagnose "graph not found" false positives when a graph folder exists but
scripts report graphs missing. Scans the known store locations — `.ua/`, legacy
`.understand-anything/`, `.gitnexus/` (GitNexus's ladybug DB), `.codegraph/`
(CodeGraph's SQLite DB), and `.docforge/tmp/` (docforge-derived, provisional)
— and reports:
  - which graph folders exist and what they contain
  - whether a code (knowledge) graph and a flow (domain) graph are present
  - file sizes and modification times
  - schema structure (nodes/edges count) for JSON graphs; a note for the
    binary ladybug/SQLite DBs (queried via their MCP tools, not read here)

Usage:
    python diagnose_graphs.py --repo <path>
    python diagnose_graphs.py --repo <path> --verbose
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

from graph_storage import KNOWN_GRAPH_DIRS

# code graph is the universal precondition; flow graph is optional (a source
# emits it, or docforge derives a provisional one into .docforge/tmp/).
# GitNexus's .gitnexus/lbug is a ladybug DB that serves both capabilities.
# CodeGraph's .codegraph/codegraph.db serves only the code graph — it has no
# flow_graph capability, so it is absent from the flow candidates below.
GRAPH_CANDIDATES = {
    "code (knowledge) graph": [
        ".ua/knowledge-graph.json",
        ".understand-anything/knowledge-graph.json",
        ".gitnexus/lbug",
        ".codegraph/codegraph.db",
    ],
    "flow (domain) graph": [
        ".ua/domain-graph.json",
        ".understand-anything/domain-graph.json",
        ".gitnexus/lbug",
        ".docforge/tmp/flow-graph.json",
    ],
}
REQUIRED = {"code (knowledge) graph"}

# Binary DB files probe_graph() cannot parse as JSON, and the note printed for
# each in --verbose output.
DB_NOTES = {
    "lbug": "ladybug DB (binary) — query via the gitnexus MCP or "
            "scripts/graph_source_gitnexus_reader.py",
    "codegraph.db": "SQLite DB (binary) — query via the codegraph MCP tool "
                     "(codegraph_explore); no offline reader",
}


def find_graph(repo: Path, candidates: list[str]) -> Path | None:
    """Search upward for graph file from repo root to git root."""
    base = repo.resolve()
    for current in (base, *base.parents):
        for relative_path in candidates:
            candidate = current / relative_path
            if candidate.is_file():
                return candidate
        if (current / ".git").exists():
            break
    return None


def probe_graph(path: Path) -> dict:
    """Load and inspect graph structure. The ladybug DB (.gitnexus/lbug) and
    CodeGraph's SQLite DB (.codegraph/codegraph.db) are binary files, not
    JSON — report them as such rather than as invalid JSON."""
    if path.name in DB_NOTES:
        return {
            "database": True,
            "size_bytes": path.stat().st_size,
            "mtime": datetime.fromtimestamp(path.stat().st_mtime).isoformat(),
        }
    try:
        with open(path) as handle:
            data = json.load(handle)

        info = {
            "valid_json": True,
            "size_bytes": path.stat().st_size,
            "mtime": datetime.fromtimestamp(path.stat().st_mtime).isoformat(),
        }
        for key in ["nodes", "files", "entities", "items"]:
            if isinstance(data.get(key), list):
                info["node_key"] = key
                info["node_count"] = len(data[key])
                break
        for key in ["edges", "links", "relationships", "flows"]:
            if isinstance(data.get(key), list):
                info["edge_key"] = key
                info["edge_count"] = len(data[key])
                break
        return info
    except Exception as error:
        return {"valid_json": False, "error": str(error)}


def list_dir(repo: Path, directory: Path) -> None:
    try:
        rel = directory.relative_to(repo)
    except ValueError:
        rel = directory
    print(f"Contents of {rel}/:")
    try:
        for item in sorted(directory.iterdir()):
            stat = item.stat()
            size = f"{stat.st_size:,} bytes" if item.is_file() else "[dir]"
            mtime = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            print(f"  {item.name:30s}  {size:15s}  {mtime}")
    except Exception as error:
        print(f"  Error reading: {error}", file=sys.stderr)
    print()


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--repo", required=True, type=Path)
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    if not args.repo.is_dir():
        print(f"Not a directory: {args.repo}", file=sys.stderr)
        return 2

    repo = args.repo.resolve()
    print(f"Repository: {repo}")
    print()

    print("Folder status:")
    present_dirs = []
    for name in KNOWN_GRAPH_DIRS:
        directory = repo / name
        exists = directory.is_dir()
        print(f"  {name + '/':28s}{' ✓ exists' if exists else ' ✗ missing'}")
        if exists:
            present_dirs.append(directory)
    print()

    for directory in present_dirs:
        list_dir(repo, directory)

    print("Graph discovery (upward search from repo root):")
    code_ok = True
    for graph_name, candidates in GRAPH_CANDIDATES.items():
        tag = "required" if graph_name in REQUIRED else "optional"
        found = find_graph(repo, candidates)
        if found:
            try:
                rel_path = found.relative_to(repo)
            except ValueError:
                rel_path = found
            print(f"  {graph_name:24s} ({tag})  ✓ found at {rel_path}")
            if args.verbose:
                info = probe_graph(found)
                if info.get("database"):
                    print(f"    - size: {info['size_bytes']:,} bytes")
                    print(f"    - mtime: {info['mtime']}")
                    print(f"    - {DB_NOTES.get(found.name, 'binary DB')}")
                elif info.get("valid_json"):
                    print(f"    - size: {info['size_bytes']:,} bytes")
                    print(f"    - mtime: {info['mtime']}")
                    if info.get("node_key"):
                        print(f"    - nodes ({info['node_key']}): {info.get('node_count', '?')}")
                    if info.get("edge_key"):
                        print(f"    - {info['edge_key']}: {info.get('edge_count', '?')}")
                else:
                    print(f"    ⚠ Invalid JSON: {info.get('error')}")
        else:
            print(f"  {graph_name:24s} ({tag})  ✗ not found")
            if graph_name in REQUIRED:
                code_ok = False

    print()
    if code_ok:
        print("✓ Code graph present. (A flow graph is optional — a source may "
              "emit one, or docforge derives a provisional one.)")
        return 0
    print("✗ No code graph found. Build one from any configured source — "
          "see references/graph-sources.md.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
