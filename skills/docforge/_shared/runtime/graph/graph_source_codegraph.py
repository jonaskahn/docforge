#!/usr/bin/env python3
"""CodeGraph graph source: detection only.

CodeGraph (https://github.com/colbymchenry/codegraph) indexes a repo into a
SQLite database at .codegraph/codegraph.db. Unlike GitNexus, it is **MCP-only**
— there is no JSON export and no offline reader docforge can open directly:

  * the codegraph MCP tool (`codegraph_explore`), available once
    `codegraph install` has wired the MCP server into the calling agent and
    `codegraph init` has built the index for this repo. There is nothing else
    — no `graph_source_codegraph_reader.{py,js}` exists, and none is planned.

CodeGraph's own file watcher keeps the index synced on every save (debounced
auto-sync) and reconciles it at MCP-connect time, so unlike GitNexus this
module does not compute staleness against git HEAD — a present db is current
by construction.

CodeGraph carries no business-flow/process concept (it is a structural
call/import/symbol graph only), so it satisfies **only** the code-graph
capability, never flow-graph.

Readiness here is only half the picture. `detect()` can confirm the db file
exists on disk, but it cannot see whether `codegraph_explore` is actually
wired into the *calling* agent's session — only the agent knows its own tool
list. So "READY" from this module means "an index exists to query," not "you
can query it right now." Before treating a codegraph result as usable, the
agent must confirm `codegraph_explore` (possibly deferred) is present in this
session's tools; if it is absent entirely, tell the user to run
`codegraph install` and restart the agent — see
references/graph/graph-source-codegraph.md.

This module exposes a SOURCE descriptor consumed by the graph_source_registry.py
registry; see references/graph/adding-a-graph-source.md for the interface.

Usage:
    python graph_source_codegraph.py detect --repo <path>
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .graph_storage import find_graph_file, relative_display_path

SOURCE_NAME = "codegraph"
DISPLAY = "CodeGraph"
CAPABILITIES = frozenset({"code_graph"})
# A SQLite DB queried exclusively through the codegraph MCP tool — no JSON
# export, no offline reader. Distinct from GitNexus's "db" mode because there
# is no graph_source_codegraph_reader to fall back to.
READ_MODE = "mcp"

DB_CANDIDATES = [".codegraph/codegraph.db"]


def detect(repo: Path) -> dict:
    """Report whether a CodeGraph index exists on disk.

    Returns the registry-standard keys code_graph / flow_graph — code_graph is
    the path to .codegraph/codegraph.db when present, else None; flow_graph is
    always None (CodeGraph has no business-flow/process capability).

    This is a pure filesystem check with no staleness computation — CodeGraph's
    own auto-sync watcher and connect-time reconciliation already keep a
    present db current, so there is nothing to re-derive here.
    """
    db = find_graph_file(repo, DB_CANDIDATES)
    return {
        "code_graph": db,
        "flow_graph": None,
    }


def setup_hint(repo: Path, gap: str) -> list[str]:
    """Lines explaining global setup separately from approved repo indexing."""
    db = detect(repo)["code_graph"]
    if not db:
        return [
            "CodeGraph (no index yet): global setup is user-run:",
            "    codegraph install   # one-time MCP wiring; restart the agent afterward",
            "  Once the tool is wired, ask explicit approval; the agent may then run:",
            "    codegraph init      # builds .codegraph/codegraph.db for this repo",
            "  Re-run detect to confirm READY (see references/graph/graph-source-codegraph.md).",
        ]
    return [
        "CodeGraph index present — .codegraph/codegraph.db is ready. Before "
        "reading it, confirm the codegraph_explore MCP tool (possibly listed as "
        "deferred) is actually in this session's tool list — a present db does "
        "not by itself mean the MCP server is wired to this agent.",
        "  If codegraph_explore is listed: load it (via tool search if deferred) and query it directly.",
        "  If it is not listed at all: ask the user to run `codegraph install` "
        "outside this agent, then restart. There is no offline reader to fall "
        "back to (see references/graph/graph-source-codegraph.md).",
    ]


def run_detect(args: argparse.Namespace) -> int:
    result = detect(args.repo)
    db = result["code_graph"]
    if db:
        print(f"READY  codegraph  -> {relative_display_path(db, args.repo)}")
        print("  On-disk index found. This does NOT confirm the codegraph_explore "
              "MCP tool is wired to the calling agent this session — check the "
              "tool list separately before reading.")
        return 0
    print("MISSING  codegraph index  (checked for .codegraph/codegraph.db)")
    for line in setup_hint(args.repo, "code_graph"):
        print(line if line.startswith("    ") else f"  {line}")
    return 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="command", required=True)

    p_detect = sub.add_parser("detect", help="check CodeGraph index state")
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
