#!/usr/bin/env python3
"""Validate and report on graph files at repository root.

Helps diagnose "graph not found" false positives when .ua/ folder exists
but scripts report graphs missing. Scans for graph files and reports:
  - Whether .ua/ folder exists
  - What files are inside it
  - Whether knowledge-graph.json and domain-graph.json are present
  - File sizes and modification times
  - Schema structure (nodes count, etc.)

Usage:
    python validate_graphs.py --repo <path>
    python validate_graphs.py --repo <path> --verbose
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

GRAPH_CANDIDATES = {
    "knowledge-graph.json": [".ua/knowledge-graph.json", ".understand-anything/knowledge-graph.json"],
    "domain-graph.json": [".ua/domain-graph.json", ".understand-anything/domain-graph.json"],
}


def find_graph(repo: Path, candidates: list[str]) -> Path | None:
    """Search upward for graph file from repo root to git root."""
    base = repo.resolve()
    for cur in (base, *base.parents):
        for rel in candidates:
            p = cur / rel
            if p.is_file():
                return p
        if (cur / ".git").exists():
            break
    return None


def probe_graph(path: Path) -> dict:
    """Load and inspect graph structure."""
    try:
        with open(path) as f:
            data = json.load(f)

        info = {
            "valid_json": True,
            "size_bytes": path.stat().st_size,
            "mtime": datetime.fromtimestamp(path.stat().st_mtime).isoformat(),
        }

        # Find node collection
        for key in ["nodes", "files", "entities", "items"]:
            if isinstance(data.get(key), list):
                info["node_key"] = key
                info["node_count"] = len(data[key])
                break

        # Find edge collection
        for key in ["edges", "links", "relationships"]:
            if isinstance(data.get(key), list):
                info["edge_key"] = key
                info["edge_count"] = len(data[key])
                break

        return info
    except Exception as e:
        return {"valid_json": False, "error": str(e)}


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

    # Check for .ua/ folder
    ua_dir = repo / ".ua"
    ua_legacy = repo / ".understand-anything"

    has_ua = ua_dir.is_dir()
    has_legacy = ua_legacy.is_dir()

    print(f"Folder status:")
    print(f"  .ua/                     {' ✓ exists' if has_ua else ' ✗ missing'}")
    print(f"  .understand-anything/    {' ✓ exists' if has_legacy else ' ✗ missing'}")
    print()

    if has_ua:
        print(f"Contents of .ua/:")
        try:
            items = sorted(ua_dir.iterdir())
            for item in items:
                stat = item.stat()
                size = f"{stat.st_size:,} bytes" if item.is_file() else "[dir]"
                mtime = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                print(f"  {item.name:30s}  {size:15s}  {mtime}")
        except Exception as e:
            print(f"  Error reading: {e}", file=sys.stderr)
        print()

    if has_legacy:
        print(f"Contents of .understand-anything/:")
        try:
            items = sorted(ua_legacy.iterdir())
            for item in items:
                stat = item.stat()
                size = f"{stat.st_size:,} bytes" if item.is_file() else "[dir]"
                mtime = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                print(f"  {item.name:30s}  {size:15s}  {mtime}")
        except Exception as e:
            print(f"  Error reading: {e}", file=sys.stderr)
        print()

    # Check for each graph type
    print(f"Graph discovery (upward search from repo root):")
    all_ok = True

    for graph_name, candidates in GRAPH_CANDIDATES.items():
        found = find_graph(repo, candidates)
        if found:
            try:
                rel_path = found.relative_to(repo)
            except ValueError:
                rel_path = found

            print(f"  {graph_name:25s}  ✓ found at {rel_path}")

            if args.verbose:
                info = probe_graph(found)
                if info.get("valid_json"):
                    print(f"    - size: {info['size_bytes']:,} bytes")
                    print(f"    - mtime: {info['mtime']}")
                    if info.get("node_key"):
                        print(f"    - nodes ({info['node_key']}): {info.get('node_count', '?')}")
                    if info.get("edge_key"):
                        print(f"    - edges ({info['edge_key']}): {info.get('edge_count', '?')}")
                else:
                    print(f"    ⚠ Invalid JSON: {info.get('error')}")
        else:
            print(f"  {graph_name:25s}  ✗ not found (checked .ua/ and .understand-anything/)")
            all_ok = False

    print()
    if all_ok:
        print("✓ All graphs found and accessible.")
        return 0
    else:
        print("✗ Some graphs missing. Run /understand and/or /understand-domain")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
