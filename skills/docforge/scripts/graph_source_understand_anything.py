#!/usr/bin/env python3
"""understand-anything graph source: detection only.

This source is always "already built" by the time docforge's Precheck sees
it — understand-anything writes .ua/knowledge-graph.json and
.ua/domain-graph.json (or the legacy .understand-anything/ path) itself, via
/understand and /understand-domain. There is no build() here, only detect().

Usage as a library:
    from graph_source_ua import detect
    result = detect(repo)  # {"knowledge_graph": Path|None, "domain_graph": Path|None}
"""

from __future__ import annotations

from pathlib import Path

from graph_common import find

SOURCE_NAME = "understand-anything"

KNOWLEDGE_GRAPH_CANDIDATES = [
    ".ua/knowledge-graph.json",
    ".understand-anything/knowledge-graph.json",
]

DOMAIN_GRAPH_CANDIDATES = [
    ".ua/domain-graph.json",
    ".understand-anything/domain-graph.json",
]


def detect(repo: Path) -> dict:
    """Look for both graph files. Either key may be None if not found."""
    return {
        "knowledge_graph": find(repo, KNOWLEDGE_GRAPH_CANDIDATES),
        "domain_graph": find(repo, DOMAIN_GRAPH_CANDIDATES),
    }
