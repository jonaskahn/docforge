#!/usr/bin/env python3
"""Source-agnostic helpers shared by every graph_source_*.py module and by
check_preconditions.py.

Nothing in this file knows which tool (understand-anything, GitNexus, or any
future source) produced a graph — it only knows how to find, display, sanity
check, and write the two on-disk files docforge itself reads:
$PROJECT_ROOT/.ua/knowledge-graph.json and $PROJECT_ROOT/.ua/domain-graph.json
(or their legacy .understand-anything/ counterparts, for reading only — new
writes always go to .ua/).
"""

from __future__ import annotations

import json
from pathlib import Path

GRAPH_DIR_NAMES = (".ua", ".understand-anything")


def find(repo: Path, candidates: list[str]) -> Path | None:
    """Search the repo root, then every ancestor up to (and including) the
    git root, for the first candidate relative path that exists as a file.

    Graphs live at $PROJECT_ROOT/...; if --repo points at a subdirectory, a
    direct lookup would falsely report "not found" even though the file
    exists at the root, so climb until a .git directory is reached.
    """
    base = repo.resolve()
    for cur in (base, *base.parents):
        for rel in candidates:
            p = cur / rel
            if p.is_file():
                return p
        if (cur / ".git").exists():
            break  # reached the repo root; do not climb past it
    return None


def display(found: Path, repo: Path) -> str:
    """Path relative to --repo when possible, else absolute (the file may
    sit at an ancestor when --repo is a subdirectory)."""
    try:
        return str(found.relative_to(repo.resolve()))
    except ValueError:
        return str(found)


def show_graph_dirs(repo: Path) -> None:
    """On a miss, list what the graph folders actually hold so a false 'not
    found' (folder present, expected file absent or misnamed) is visible at a
    glance. Points at validate_graphs.py for the full probe."""
    base = repo.resolve()
    listed = False
    for cur in (base, *base.parents):
        for name in GRAPH_DIR_NAMES:
            d = cur / name
            if d.is_dir():
                try:
                    names = sorted(p.name for p in d.iterdir())
                except OSError as e:
                    names = [f"(error listing: {e})"]
                print(f"  {name}/ exists at {display(d, repo)} — contains: "
                      f"{', '.join(names) or '(empty)'}")
                listed = True
        if (cur / ".git").exists():
            break
    if listed:
        print("  Diagnose: python scripts/validate_graphs.py --repo . --verbose")


def validate_knowledge_graph_shape(obj: dict) -> str | None:
    """Minimal sanity check for a freshly-built knowledge graph, before it is
    written to disk. Returns an error string, or None if the shape is
    acceptable. Deliberately loose — docforge's own reader (graph_extract.py)
    already tolerates several key names; this only catches a build gone
    obviously wrong (empty or malformed), not schema drift."""
    if not isinstance(obj, dict):
        return "knowledge graph must be a JSON object"
    nodes = obj.get("nodes")
    edges = obj.get("edges")
    if not isinstance(nodes, list) or not nodes:
        return "knowledge graph must have a non-empty 'nodes' list"
    if not isinstance(edges, list):
        return "knowledge graph must have an 'edges' list (may be empty)"
    return None


def validate_domain_graph_shape(obj: dict) -> str | None:
    """domain-graph.json has no rigid consumer today (no docforge script
    parses it directly) — only confirm it is a non-empty JSON object."""
    if not isinstance(obj, dict) or not obj:
        return "domain graph must be a non-empty JSON object"
    return None


def write_graph(repo: Path, knowledge_graph: dict, domain_graph: dict) -> tuple[Path, Path]:
    """Write both graph files to $PROJECT_ROOT/.ua/, creating the directory
    if needed. Raises ValueError if either shape fails its sanity check —
    callers should surface that message and write nothing."""
    kg_error = validate_knowledge_graph_shape(knowledge_graph)
    if kg_error:
        raise ValueError(f"refusing to write knowledge graph: {kg_error}")
    dg_error = validate_domain_graph_shape(domain_graph)
    if dg_error:
        raise ValueError(f"refusing to write domain graph: {dg_error}")

    ua_dir = repo.resolve() / ".ua"
    ua_dir.mkdir(parents=True, exist_ok=True)

    kg_path = ua_dir / "knowledge-graph.json"
    dg_path = ua_dir / "domain-graph.json"
    kg_path.write_text(json.dumps(knowledge_graph, indent=2) + "\n", encoding="utf-8")
    dg_path.write_text(json.dumps(domain_graph, indent=2) + "\n", encoding="utf-8")
    return kg_path, dg_path
