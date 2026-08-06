#!/usr/bin/env python3
"""Source-agnostic graph-file storage helpers shared by every graph_source_*.py
module, by the graph_source_registry.py registry, by precheck_graph.py, and by
derive_flow_graph.py.

Nothing in this file knows which tool (understand-anything, GitNexus, or any
future source) produced a graph — it only knows how to find, display, sanity
check, and write graph files on disk. There is no single canonical store: each
source declares where its own graph lives (understand-anything reads .ua/,
GitNexus stores a ladybug DB under .gitnexus/, CodeGraph stores a SQLite DB
under .codegraph/, and docforge's own derived flow graph is written to the
never-committed .docforge/tmp/).
"""

from __future__ import annotations

import json
from pathlib import Path

from runtime.common.python._util import ensure_docforge_gitignore, ensure_gitignored_dir

# Directories a graph file may live in, for diagnostics only. Detection itself
# is per-source (each source declares its own candidate paths); this list is
# used solely to list folder contents on a miss.
KNOWN_GRAPH_DIRS = (".ua", ".understand-anything", ".gitnexus", ".codegraph", ".docforge/tmp")


def find_graph_file(repo: Path, candidates: list[str]) -> Path | None:
    """Search the repo root, then every ancestor up to the project root
    (a .git or .docforge directory), for the first candidate relative path
    that exists as a file.

    Graphs live at $PROJECT_ROOT/...; if --repo points at a subdirectory, a
    direct lookup would falsely report "not found" even though the file
    exists at the root, so climb until the project root is reached. A
    .docforge directory counts too, not just .git, so a repository root with
    no git of its own still stops the climb instead of searching unrelated
    ancestor directories.
    """
    base = repo.resolve()
    for current in (base, *base.parents):
        for relative_path in candidates:
            candidate = current / relative_path
            if candidate.is_file():
                return candidate
        if (current / ".git").exists() or (current / ".docforge").exists():
            break  # reached the project root; do not climb past it
    return None


def relative_display_path(found: Path, repo: Path) -> str:
    """Path relative to --repo when possible, else absolute (the file may
    sit at an ancestor when --repo is a subdirectory)."""
    try:
        return str(found.relative_to(repo.resolve()))
    except ValueError:
        return str(found)


def list_known_graph_dirs(repo: Path) -> None:
    """On a miss, list what the known graph folders actually hold so a false
    'not found' (folder present, expected file absent or misnamed) is visible
    at a glance. Points at diagnose_graphs.py for the full probe."""
    base = repo.resolve()
    listed = False
    for current in (base, *base.parents):
        for name in KNOWN_GRAPH_DIRS:
            directory = current / name
            if directory.is_dir():
                try:
                    names = sorted(entry.name for entry in directory.iterdir())
                except OSError as error:
                    names = [f"(error listing: {error})"]
                print(f"  {name}/ exists at {relative_display_path(directory, repo)} — contains: "
                      f"{', '.join(names) or '(empty)'}")
                listed = True
        if (current / ".git").exists() or (current / ".docforge").exists():
            break
    if listed:
        print("  Diagnose: python runtime/cli/python/diagnose_graphs.py --repo . --verbose")


def validate_flow_graph_shape(flow_graph: dict) -> str | None:
    """Sanity check for a flow graph before it is written — today
    only docforge's own derivation writes one. It uses the docforge flow
    shape: a non-empty 'flows' list of objects, each with a 'name' and a
    'steps' list. Refusing an empty graph is what stops a derivation gone
    wrong from masquerading as a real flow graph."""
    if not isinstance(flow_graph, dict):
        return "flow graph must be a JSON object"
    flows = flow_graph.get("flows")
    if not isinstance(flows, list) or not flows:
        return "flow graph must have a non-empty 'flows' list"
    for index, flow in enumerate(flows):
        if not isinstance(flow, dict) or not flow.get("name"):
            return f"flow[{index}] must be an object with a non-empty 'name'"
        if not isinstance(flow.get("steps"), list):
            return f"flow[{index}] ('{flow.get('name')}') must have a 'steps' list"
    return None


def _write_json(path: Path, graph: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(graph, indent=2) + "\n", encoding="utf-8")


def write_flow_graph(repo: Path, flow_graph: dict, dest_rel: str = ".docforge/tmp") -> Path:
    """Write a flow graph to $PROJECT_ROOT/<dest_rel>/flow-graph.json.
    Docforge's derivation passes dest_rel='.docforge/tmp' (never committed).
    Raises ValueError if the shape fails its sanity check — callers should
    surface that message and write nothing."""
    error = validate_flow_graph_shape(flow_graph)
    if error:
        raise ValueError(f"refusing to write flow graph: {error}")
    path = repo.resolve() / dest_rel / "flow-graph.json"
    _write_json(path, flow_graph)
    return path


def ensure_tmp_dir_gitignored(repo: Path) -> Path:
    """Drop $PROJECT_ROOT/.docforge/.gitignore and .docforge/tmp/.gitignore containing '*' so the
    provisional derived flow graph is never committed. Idempotent."""
    ensure_docforge_gitignore(repo.resolve() / ".docforge")
    return ensure_gitignored_dir(repo.resolve() / ".docforge" / "tmp")
