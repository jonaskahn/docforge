#!/usr/bin/env python3
"""Scale-aware flow budgets shared by the flow runtimes. Not a public CLI.

A flat budget systematically under-covers large repos: plugilo-api is
`project.scale.class = "large"` (900 source files) with 1,300 entry points,
so a budget of 15 covered 1.1% of the surface. The two knobs scale
separately, read from the authoritative `project.scale.class` already
recorded in the manifest (user overrides land in `class`, so it is never
re-derived here):

| scale.class | --max-flows default | --main-limit default |
|---|---|---|
| small  | 15 | 15 |
| medium | 30 | 25 |
| large  | 50 | 40 |
| missing / unknown / pre-init | 15 | 15 |

`--max-flows` is the candidate surface (grows with repo breadth);
`--main-limit` is the deep-dive document budget (bounded by review cost;
overflow is deferred, not dropped). An explicit value > 0 always wins;
explicit 0 / negative / null counts as "not passed" and falls back to the
scale default (documented in help text). Mirrors budgets.js.
"""

from __future__ import annotations

import json
from pathlib import Path

MAX_FLOWS_BY_SCALE = {"small": 15, "medium": 30, "large": 50}
MAIN_LIMIT_BY_SCALE = {"small": 15, "medium": 25, "large": 40}
FALLBACK_MAX_FLOWS = 15
FALLBACK_MAIN_LIMIT = 15


def scale_class(repo: Path) -> str | None:
    """`manifest.json → project.scale.class`, or None on a missing/malformed
    manifest or an unknown class."""
    try:
        manifest = json.loads((repo / ".docforge" / "manifest.json").read_text(encoding="utf-8"))
        scale = manifest.get("project", {}).get("scale")
        if not isinstance(scale, dict):
            return None
        klass = scale.get("class")
        return str(klass) if klass in MAX_FLOWS_BY_SCALE else None
    except (OSError, ValueError):
        return None


def _budget_for(repo: Path, by_scale: dict, fallback: int, explicit: int | None) -> int:
    if explicit is not None and explicit > 0:
        return explicit
    klass = scale_class(repo)
    return by_scale.get(klass, fallback) if klass else fallback


def max_flows_for(repo: Path, explicit: int | None = None) -> int:
    return _budget_for(repo, MAX_FLOWS_BY_SCALE, FALLBACK_MAX_FLOWS, explicit)


def main_limit_for(repo: Path, explicit: int | None = None) -> int:
    return _budget_for(repo, MAIN_LIMIT_BY_SCALE, FALLBACK_MAIN_LIMIT, explicit)
