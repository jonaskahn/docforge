#!/usr/bin/env python3
"""understand-anything graph source: detection only.

understand-anything writes .ua/knowledge-graph.json (code graph) and
.ua/domain-graph.json (flow graph) itself — or the legacy .understand-anything/
path — via /understand and /understand-domain. docforge reads those files
directly (zero-copy), so there is no build() here, only detect() and the
setup hints for when a needed graph is absent.

This module exposes a SOURCE descriptor consumed by the graph_source_registry.py
registry; see references/graph/adding-a-graph-source.md for the interface.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from .graph_storage import find_graph_file

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

# Tags that mark a re-export shim (index.js barrels), not real flow logic —
# excluded from entry-point seeds so they never crowd out true entry surfaces.
NOISE_TAGS = frozenset({"barrel", "re-export"})
ENTRY_NAME = re.compile(
    r"^(?:[Aa]ggregate|[Tt]rack|[Pp]ublish|[Dd]ispatch|[Ee]xecute|"
    r"[Rr]un|[Ss]tart|[Rr]eceive|[Pp]rocess|[Cc]onsume|[Hh]andle|"
    r"[Cc]reate|[Uu]pdate|[Dd]elete|[Ss]ave|[Gg]et|[Pp]ost|[Pp]ut|"
    r"[Pp]atch|[Ss]end)(?:[A-Z0-9_]|$)",
)
CORE_ENTRY_NAME = re.compile(
    r"^(?:[Aa]ggregate|[Tt]rack|[Pp]ublish|[Dd]ispatch|[Ee]xecute|"
    r"[Rr]un|[Ss]tart|[Rr]eceive|[Pp]rocess|[Cc]onsume|[Hh]andle)"
    r"(?:[A-Z0-9_]|$)",
)
SURFACE_NAME = re.compile(
    r"(controller|handler|processor|consumer|listener|worker|job|command|aggregator)$",
    re.IGNORECASE,
)
ENTRY_PATH = re.compile(
    r"(controllers?|handlers?|processors?|consumers?|workers?|jobs?|commands?|"
    r"aggregators?|routes?|endpoints?)",
    re.IGNORECASE,
)


def detect(repo: Path) -> dict:
    """Locate this source's graphs. Either key may be None if not found."""
    return {
        "code_graph": find_graph_file(repo, CODE_GRAPH_CANDIDATES),
        "flow_graph": find_graph_file(repo, FLOW_GRAPH_CANDIDATES),
    }


def _service_layer_ids(doc: dict) -> set:
    """Node ids belonging to a layer whose name reads as a service/business
    layer — a strong 'this is where flows live' signal in the UA graph."""
    ids: set = set()
    for layer in doc.get("layers", []) if isinstance(doc, dict) else []:
        if not isinstance(layer, dict):
            continue
        name = str(layer.get("name", "")).lower()
        if any(word in name for word in ("service", "business", "domain", "application", "presentation", "api")):
            for nid in layer.get("nodeIds", []) or []:
                ids.add(nid)
    return ids


def entry_points(repo: Path) -> list[dict]:
    """Ranked entry-point seeds for flow derivation, read from the UA code
    graph's own semantic signal — never a full-graph scan.

    Signal, in priority order (see references/graph/flow-derivation.md):
      api-handler tag        → the request entry surface
      service / pipeline type→ business-logic entry
      entry-point tag        → declared entry (minus barrel re-exports)
      step type              → a pipeline stage
    Each is boosted by Service-layer membership and by outgoing-edge fan-out
    (how much the node reaches). Returns [] when the graph carries no such
    signal, so the caller falls back to a full dump.
    """
    path = find_graph_file(repo, CODE_GRAPH_CANDIDATES)
    if not path:
        return []
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    if not isinstance(doc, dict):
        return []

    nodes = doc.get("nodes") or []
    edges = doc.get("edges") or []
    service_ids = _service_layer_ids(doc)

    fanout: dict = {}
    for edge in edges:
        if isinstance(edge, dict):
            src = edge.get("source")
            if src is not None:
                fanout[src] = fanout.get(src, 0) + 1

    seeds: list[dict] = []
    for node in nodes:
        if not isinstance(node, dict):
            continue
        tags = {str(t).lower() for t in (node.get("tags") or [])}
        node_type = str(node.get("type", "")).lower()
        if tags & NOISE_TAGS:
            continue

        nid = node.get("id")
        if "api-handler" in tags:
            tier = 1000
        elif node_type in ("service", "pipeline"):
            tier = 800
        elif "entry-point" in tags:
            tier = 600
        elif node_type == "step":
            tier = 300
        elif (
            (
                node_type == "class"
                and SURFACE_NAME.search(str(node.get("name", "")))
                and (
                    nid in service_ids
                    or ENTRY_PATH.search(str(node.get("filePath", "")))
                )
            )
            or (
                node_type == "function"
                and (
                    (
                        ENTRY_PATH.search(str(node.get("filePath", "")))
                        and ENTRY_NAME.search(str(node.get("name", "")))
                    )
                    or (
                        nid in service_ids
                        and CORE_ENTRY_NAME.search(str(node.get("name", "")))
                    )
                )
            )
        ):
            # UA knowledge graphs may expose only file/class/function nodes and
            # containment edges. Layer, path, and entry-like naming are then
            # candidate signals; they are not mislabeled as native flows.
            tier = 200
        else:
            continue

        rank = tier + (200 if nid in service_ids else 0) + fanout.get(nid, 0)
        seeds.append({
            "id": nid,
            "name": node.get("name"),
            "kind": node.get("type"),
            "path": node.get("filePath"),
            "rank": rank,
        })

    seeds.sort(key=lambda s: -s["rank"])
    return seeds


def setup_hint(repo: Path, gap: str) -> list[str]:
    """Lines telling the user how to produce the missing graph with this
    source. `gap` is 'code_graph' or 'flow_graph'."""
    if gap == "flow_graph":
        return [
            "Understand-Anything: after explicit approval and once the code graph exists, the agent may run:",
            "    /understand-domain",
        ]
    return [
        "Understand-Anything: confirm the understand-anything skill is loaded "
        "in this session. After disclosing first-run cost and receiving explicit approval, the agent may run:",
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
    "entry_points": entry_points,
}
