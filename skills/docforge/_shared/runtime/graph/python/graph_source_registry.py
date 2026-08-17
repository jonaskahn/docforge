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

Which resolver to call:
    resolve_locked()      what every step after `init` wants — honors the
                          provider the user chose and recorded in
                          manifest["graph"], falling back to priority order only
                          when no lock exists.
    resolve_first_ready() priority order, lock-blind. Only for callers that run
                          *before* a lock exists, or that deliberately ignore it.
    resolve_all_ready()   every ready source, so precheck_graph can present the
                          choice that creates the lock.
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


def source_by_name(name: str) -> dict | None:
    """The registry descriptor for a provider id, or None if unregistered."""
    for source in SOURCES:
        if source["name"] == name:
            return source
    return None


def read_graph_lock(repo: Path) -> dict | None:
    """The session's locked graph record (`manifest["graph"]`), or None when
    there is no manifest, no lock, or the manifest cannot be read.

    Located with find_graph_file so the lock resolves from the same project root
    every source's detect() resolves graphs against: when --repo points at a
    subdirectory, a direct lookup would miss the lock and silently fall back to
    priority order, which is the very substitution this function prevents.

    Never raises. A repo that was never `init`ed still has to work — flow
    derivation and harvest fall back to registry priority there — so a missing
    or legacy manifest is an absent lock, not an error. Importing the manifest
    loader (not manage_manifest) keeps this cycle-free: manage_manifest imports
    this registry, never the reverse."""
    from ...common.python._util import load_manifest
    from .graph_storage import find_graph_file

    found = find_graph_file(repo, [".docforge/manifest.json"])
    if found is None:
        return None
    try:
        # json.JSONDecodeError subclasses ValueError, so this covers a corrupt
        # manifest as well as a missing or unsupported-version one.
        manifest = load_manifest(found)
    except (ValueError, OSError):
        return None
    lock = manifest.get("graph")
    if not isinstance(lock, dict) or not lock.get("provider"):
        return None
    return lock


def flow_capability_of(repo: Path, provider: str) -> str:
    """The flow capability of one named provider: "native", "derived", or "none".

    Answers "what can *this* provider offer", never "does any provider have flows"
    — the repo-wide question recorded flow: "native" for a session locked to
    CodeGraph merely because an unrelated .ua/domain-graph.json existed. CodeGraph
    advertises no flow_graph, and references/graph/graph-sources.md is explicit
    that a selected primary without native flows must read "Docforge-derived
    (provisional)", never "Native flow source: CodeGraph"."""
    from .graph_storage import DERIVED_FLOW_CANDIDATES, find_graph_file

    source = source_by_name(provider)
    if source and "flow_graph" in source["capabilities"] and source["detect"](repo).get("flow_graph"):
        return "native"
    if find_graph_file(repo, DERIVED_FLOW_CANDIDATES):
        return "derived"
    return "none"


def resolve_locked(repo: Path, capability: str) -> tuple[dict | None, Path | None, str]:
    """Resolve `capability` honoring the session's locked provider.

    The lock is the user's answered choice (see references/graph/graph-sources.md
    "Session persistence"): once `init` records it, every later step uses that
    provider instead of re-detecting. Registry priority applies only when no lock
    exists — otherwise a repo with two graphs would silently analyze the one the
    user declined.

    Returns (source, path, origin) where origin is one of:
        "lock"            the locked provider supplies `capability`; path is its artifact
        "priority"        no lock recorded; fell back to registry order
        "lock-stale"      a lock exists but its provider has no artifact on disk;
                          source is the locked descriptor, path is None
        "lock-uncapable"  the locked provider does not advertise `capability` at
                          all (codegraph has no flow_graph, for one); path is None

    Callers decide what each origin means for them — a stale lock is an error
    worth stopping for, while "uncapable" is the normal "derive it instead"
    signal. This never raises and never silently substitutes another provider."""
    lock = read_graph_lock(repo)
    if lock is None:
        source, path = resolve_first_ready(repo, capability)
        return source, path, "priority"
    locked = source_by_name(str(lock["provider"]))
    if locked is None:
        # The manifest names a provider this registry no longer knows (removed
        # source, or an index written by a newer docforge). Treat it as stale
        # rather than guessing a replacement.
        return None, None, "lock-stale"
    if capability not in locked["capabilities"]:
        return locked, None, "lock-uncapable"
    found = locked["detect"](repo).get(capability)
    if not found:
        return locked, None, "lock-stale"
    return locked, found, "lock"
