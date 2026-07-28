#!/usr/bin/env python3
"""GitNexus graph source: detection only.

GitNexus (https://github.com/abhigyanpatwari/GitNexus) stores its graph in a
ladybug property-graph database at .gitnexus/lbug, with a sidecar
.gitnexus/meta.json describing the index (files/nodes/edges/processes counts and
the commit it was built at). docforge reads that database **directly**, in place
— there is no copy-to-JSON bridge:

  * primary  — the gitnexus MCP tools (`cypher`, `query`, `context`) and
               `gitnexus://repo/{name}/...` resources, available whenever the
               GitNexus plugin is loaded;
  * offline  — scripts/graph_source_gitnexus_reader.{py,js}, which opens
               .gitnexus/lbug via @ladybugdb/core (Node) or the ladybug Python
               binding, for machines without the MCP wired.

Because GitNexus carries native Process nodes (execution flows) and Community
clusters (functional areas), it satisfies **both** the code-graph and the
flow-graph capability the moment its index exists — no derivation, no build.

So this module is pure detection: is there an index, what does it promise, and
is it stale against the current git HEAD? See references/graph-source-gitnexus.md
for the read recipes and the capability dispatch in references/graph-sources.md.

This module exposes a SOURCE descriptor consumed by the graph_source_registry.py
registry; see references/adding-a-graph-source.md for the interface.

Usage:
    python graph_source_gitnexus.py detect --repo <path>
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from graph_storage import find_graph_file, relative_display_path

SOURCE_NAME = "gitnexus"
DISPLAY = "GitNexus"
CAPABILITIES = frozenset({"code_graph", "flow_graph"})
# A ladybug DB, not a JSON file: read via the gitnexus MCP or the offline
# reader (graph_source_gitnexus_reader.py), never via read_graph.py.
READ_MODE = "db"

LBUG_CANDIDATES = [".gitnexus/lbug"]
INDEX_MARKER_CANDIDATES = [".gitnexus/meta.json"]


def _git_head(repo: Path) -> str | None:
    try:
        out = subprocess.run(
            ["git", "-C", str(repo), "rev-parse", "HEAD"],
            capture_output=True, text=True, timeout=5,
        )
        if out.returncode == 0:
            return out.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        pass
    return None


def _read_meta(index_path: Path) -> dict | None:
    try:
        return json.loads(index_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def detect(repo: Path) -> dict:
    """Report the GitNexus graph's readiness, read directly from disk.

    Returns the registry-standard keys code_graph / flow_graph — each the path
    to the ladybug DB (.gitnexus/lbug) when that capability is available, or
    None — plus source-private fields:
      index  — Path to .gitnexus/meta.json, or None
      stats  — the index's stats dict (files/nodes/edges/processes/...), or None
      stale  — True if meta.lastCommit differs from the current git HEAD

    The DB satisfies code_graph when it has nodes and flow_graph when it has
    processes; when the sidecar meta.json carries no stats we do not
    second-guess a present DB, and report both capabilities.
    """
    lbug = find_graph_file(repo, LBUG_CANDIDATES)
    index = find_graph_file(repo, INDEX_MARKER_CANDIDATES)
    meta = _read_meta(index) if index else None
    stats = meta.get("stats") if isinstance(meta, dict) else None
    stats = stats if isinstance(stats, dict) else None

    stale = None
    if isinstance(meta, dict) and meta.get("lastCommit"):
        head = _git_head(repo)
        if head:
            stale = head != meta.get("lastCommit")

    has_nodes = stats is None or stats.get("nodes", 0) > 0
    has_processes = stats is None or stats.get("processes", 0) > 0
    return {
        "code_graph": lbug if (lbug and has_nodes) else None,
        "flow_graph": lbug if (lbug and has_processes) else None,
        "index": index,
        "stats": stats,
        "stale": stale,
    }


def setup_hint(repo: Path, gap: str) -> list[str]:
    """Lines telling the user how to produce the missing graph with GitNexus.
    The right steps depend on whether an index exists and whether it is stale."""
    info = detect(repo)
    index, stale = info["index"], info["stale"]
    if not index:
        return [
            "GitNexus (no index yet): global MCP setup is user-run when needed:",
            "    npx gitnexus setup",
            "  After explicit approval, the agent may build the repo index with:",
            "    npx gitnexus analyze",
            "  Re-run detect to confirm READY (see references/graph-source-gitnexus.md).",
        ]
    if stale:
        return [
            "GitNexus (index is STALE — meta.lastCommit != current HEAD): ask explicit approval, then re-index:",
            "    npx gitnexus analyze",
            "  Then re-run detect (see references/graph-source-gitnexus.md).",
        ]
    return [
        "GitNexus index present and current — the ladybug DB (.gitnexus/lbug) is "
        "ready. Read it via the gitnexus MCP, or offline with "
        "scripts/graph_source_gitnexus_reader.py (references/graph-source-gitnexus.md).",
    ]


def run_detect(args: argparse.Namespace) -> int:
    result = detect(args.repo)
    if result["index"] or result["code_graph"]:
        target = result["code_graph"] or result["index"]
        stale = " (STALE vs HEAD)" if result["stale"] else ""
        print(f"READY  gitnexus  -> {relative_display_path(target, args.repo)}{stale}")
        if result["stats"]:
            stats = result["stats"]
            print(f"  stats: {stats.get('nodes', '?')} nodes, {stats.get('edges', '?')} edges, "
                  f"{stats.get('processes', '?')} processes")
        print("  Read via the gitnexus MCP, or offline with "
              "scripts/graph_source_gitnexus_reader.py.")
        return 0
    print("MISSING  gitnexus index  (checked for .gitnexus/lbug and .gitnexus/meta.json)")
    for line in setup_hint(args.repo, "code_graph"):
        print(line if line.startswith("    ") else f"  {line}")
    return 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="command", required=True)

    p_detect = sub.add_parser("detect", help="check GitNexus index state")
    p_detect.add_argument("--repo", required=True, type=Path)
    p_detect.set_defaults(func=run_detect)

    args = ap.parse_args()
    if not args.repo.is_dir():
        print(f"Not a directory: {args.repo}", file=sys.stderr)
        return 2
    return args.func(args)


SOURCE = {
    "name": SOURCE_NAME,
    "display": DISPLAY,
    "capabilities": CAPABILITIES,
    "read_mode": READ_MODE,
    "detect": detect,
    "setup_hint": setup_hint,
}


if __name__ == "__main__":
    raise SystemExit(main())
