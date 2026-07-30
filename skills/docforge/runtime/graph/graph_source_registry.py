#!/usr/bin/env python3
"""Graph source registry — the single ordered list of graph producers docforge
knows about, plus the helpers that resolve a capability to a concrete graph.

This is the whole extensibility surface on the script side: to add a source
(codegraph, graphify, …) write a graph_source_<name>.py exposing a SOURCE
descriptor and append it to SOURCES here — nothing else in precheck_graph.py
or read_graph.py changes. See references/graph/adding-a-graph-source.md.

A SOURCE descriptor is a dict:
    {
      "name": str,                # stable id, e.g. "understand-anything"
      "display": str,             # human label
      "capabilities": set[str],   # subset of {"code_graph", "flow_graph"}
      "read_mode": str,           # "json" (read with read_graph.py), "db"
                                  #   (query via a native interface / optional
                                  #   offline reader), or "mcp" (query via a
                                  #   native interface only — no offline reader)
      "detect": callable(repo) -> {"code_graph": Path|None, "flow_graph": Path|None, ...},
      "setup_hint": callable(repo, gap) -> list[str],
      "entry_points": callable(repo) -> list[dict]  # OPTIONAL
    }

The optional "entry_points" hook returns ranked flow-derivation seeds —
[{"id", "name", "kind", "path", "rank"}], highest rank first — read from the
source's own entry-point signal (routes, exported-uncalled functions,
entry-point tags…), never a full scan. derive_flow_graph uses it to build an
entry-point-first, main-flow-first context instead of dumping the whole graph;
a source without it falls back to the flat dump. See
references/graph/flow-derivation.md.

Capabilities:
    code_graph  — structure and call/import relationships. Docforge's universal precondition.
    flow_graph  — business flows and ordered steps. Optional per source; if no
                  source supplies one, docforge derives a provisional one from
                  the code graph (see derive_flow_graph.py).
"""

from __future__ import annotations

from pathlib import Path

from . import graph_source_understand_anything as understand_anything
from . import graph_source_gitnexus as gitnexus
from . import graph_source_codegraph as codegraph

# Priority order: the first source that resolves a capability wins when the
# caller wants a single answer. resolve_all_ready() exposes every ready source
# so the orchestrator can let the user choose.
SOURCES = [understand_anything.SOURCE, gitnexus.SOURCE, codegraph.SOURCE]


def sources_providing(capability: str) -> list[dict]:
    """Every registered source that advertises `capability`, in priority order."""
    return [s for s in SOURCES if capability in s["capabilities"]]


def resolve_first_ready(repo: Path, capability: str) -> tuple[dict | None, Path | None]:
    """Return (source, path) for the first source that actually has `capability`
    built on disk, else (None, None). Never triggers a build."""
    for source in sources_providing(capability):
        found = source["detect"](repo).get(capability)
        if found:
            return source, found
    return None, None


def resolve_all_ready(repo: Path, capability: str) -> list[tuple[dict, Path]]:
    """Every source that actually has `capability` on disk, in priority order,
    as (source, path) pairs. Empty when none is ready. Lets the caller present
    a choice when more than one source is available for the same repo."""
    ready: list[tuple[dict, Path]] = []
    for source in sources_providing(capability):
        found = source["detect"](repo).get(capability)
        if found:
            ready.append((source, found))
    return ready


def setup_hints_for_missing(repo: Path, capability: str) -> list[tuple[dict, list[str]]]:
    """For a miss: every capable source paired with its remediation block, so
    the caller can present all options rather than a hardcoded pair."""
    return [(src, src["setup_hint"](repo, capability)) for src in sources_providing(capability)]
