#!/usr/bin/env python3
"""understand-anything graph source: detection only.

understand-anything writes .ua/knowledge-graph.json (code graph) and
.ua/domain-graph.json (flow graph) itself — or the legacy .understand-anything/
path — via /understand and /understand-domain. docforge reads those files
directly (zero-copy), so there is no build() here, only detect() and the
setup hints for when a needed graph is absent.

This module exposes a SOURCE descriptor consumed by the graph_source_registry.py
registry; see references/adding-a-graph-source.md for the interface.
"""

from __future__ import annotations

from pathlib import Path

from graph_storage import find_graph_file

SOURCE_NAME = "understand-anything"
DISPLAY = "Understand-Anything"
CAPABILITIES = frozenset({"code_graph", "flow_graph"})
# JSON graphs on disk: read offline with read_graph.py, no external interface.
READ_MODE = "json"

CODE_GRAPH_CANDIDATES = [
    ".ua/knowledge-graph.json",
    ".understand-anything/knowledge-graph.json",
]

FLOW_GRAPH_CANDIDATES = [
    ".ua/domain-graph.json",
    ".understand-anything/domain-graph.json",
]


def detect(repo: Path) -> dict:
    """Locate this source's graphs. Either key may be None if not found."""
    return {
        "code_graph": find_graph_file(repo, CODE_GRAPH_CANDIDATES),
        "flow_graph": find_graph_file(repo, FLOW_GRAPH_CANDIDATES),
    }


def setup_hint(repo: Path, gap: str) -> list[str]:
    """Lines telling the user how to produce the missing graph with this
    source. `gap` is 'code_graph' or 'flow_graph'."""
    if gap == "flow_graph":
        return [
            "Understand-Anything: after the code graph exists, run:",
            "    /understand-domain",
        ]
    return [
        "Understand-Anything: confirm the understand-anything skill is loaded "
        "in this session (check the skill listing, or load/invoke it), then run:",
        "    /understand   (or /understand <subdir> to scope; first runs on "
        "large repos consume tokens — say so before starting)",
    ]


SOURCE = {
    "name": SOURCE_NAME,
    "display": DISPLAY,
    "capabilities": CAPABILITIES,
    "read_mode": READ_MODE,
    "detect": detect,
    "setup_hint": setup_hint,
}
