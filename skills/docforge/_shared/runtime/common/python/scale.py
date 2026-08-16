#!/usr/bin/env python3
"""Three-way project-scale classification shared by intake discovery and
manifest backfill. Not a public CLI.

Classifies a repository `small | medium | large` from one existing walk
(`detect_profiles.inventory`) plus the confirmed-profile count detection
already produces, so no caller re-traverses the tree and no new ignore rules
exist. Declared-dependency breadth (`manifest_deps.extract_dependencies`) and
flow breadth (`.docforge/flow-index.json` when present) promote a class at
most one step above its source-file class — they never demote. The profile
count still nudges boundary-adjacent repos. `suggested_layout` follows the
class; a user override is recorded on the manifest and never re-derived.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

from runtime.catalog.python import detect_profiles
from runtime.common.python import manifest_deps

SMALL_MAX_SOURCE_FILES = 49
MEDIUM_MAX_SOURCE_FILES = 200
DEP_NUDGE_SMALL = 40
DEP_NUDGE_MEDIUM = 200
FLOW_NUDGE_SMALL = 10
FLOW_NUDGE_MEDIUM = 40
BOUNDARY_NUDGE_RATIO = 0.20
PROFILE_NUDGE_THRESHOLD = 3

SOURCE_SUFFIXES = {
    ".c", ".cc", ".cpp", ".cs", ".dart", ".go", ".gradle", ".h", ".hpp",
    ".java", ".js", ".jsx", ".kt", ".kts", ".m", ".mm", ".php", ".py", ".rb",
    ".rs", ".sh", ".sol", ".swift", ".ts", ".tsx",
}

LAYOUT_BY_CLASS = {"small": "compact", "medium": "standard", "large": "standard"}

COMPACT_TIERS = {"spine", "diligence"}


class LayoutTierError(ValueError):
    """An explicitly requested layout the tier does not permit."""


def layout_for(tier: str, layout: str, *, explicit: bool) -> tuple[str, str]:
    """Resolve the layout a tier permits, as `(layout, decided_by)`.

    Portfolio is the whole point of this function: its value is per-member
    separation — an inventory row and a system-context view per repository —
    so folding the collection layer into one file erases exactly the
    distinctions the tier exists to make. Compact therefore covers Spine and
    Diligence only.

    An explicit compact pick at Portfolio raises instead of being coerced: a
    user decision is never silently rewritten. A *detected* compact layout is
    forced to standard and says so via `tier-constraint`, because a small
    collection root would otherwise inherit compact from `LAYOUT_BY_CLASS`.
    """
    if layout != "compact" or tier in COMPACT_TIERS:
        return layout, "user" if explicit else "detected"
    if explicit:
        raise LayoutTierError(
            f"{tier} tier requires standard layout; "
            "compact covers spine and diligence only"
        )
    return "standard", "tier-constraint"


def _nudge_eligible(source_files: int, boundary: int) -> bool:
    """True when `source_files` sits within BOUNDARY_NUDGE_RATIO below a class
    boundary (e.g. 40-49 source files under the small/medium boundary of 50)."""
    return source_files >= math.ceil(boundary * (1 - BOUNDARY_NUDGE_RATIO))


def _flow_candidates(repo: Path) -> int:
    """Rows in the harvested flow index, or 0 when no index exists yet. A
    single read-only file read — never a tree walk."""
    index_path = repo / ".docforge" / "flow-index.json"
    try:
        data = json.loads(index_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return 0
    summary = data.get("summary") if isinstance(data, dict) else None
    if isinstance(summary, dict) and isinstance(summary.get("total"), int):
        return summary["total"]
    flows = data.get("flows") if isinstance(data, dict) else None
    return len(flows) if isinstance(flows, list) else 0


def compute_scale(
    repo: Path,
    files: list[tuple[str, Path]] | None = None,
    detections: list[dict] | None = None,
    dependencies: dict | None = None,
) -> dict:
    """Pass `files`, `detections`, and/or `dependencies` when the caller
    already has them — all derive from the same single `inventory(repo)`
    walk."""
    if files is None:
        files = detect_profiles.inventory(repo)
    tracked_files = len(files)
    source_files = sum(
        1
        for _relative, path in files
        if path.suffix.lower() in SOURCE_SUFFIXES
    )
    if detections is None:
        detections = detect_profiles.detect(repo, persist=False, files=files)
    confirmed_profiles = sum(
        1 for item in detections if item.get("confidence") == "confirmed"
    )
    if dependencies is None:
        dependencies = manifest_deps.extract_dependencies(files)
    declared_dependencies = sum(len(keys) for keys in dependencies.values())
    flow_candidates = _flow_candidates(repo)
    if source_files <= SMALL_MAX_SOURCE_FILES:
        scale_class = "small"
    elif source_files <= MEDIUM_MAX_SOURCE_FILES:
        scale_class = "medium"
    else:
        scale_class = "large"
    # Dependency and flow breadth promote at most one class above the
    # source-file class; the profile count nudges boundary-adjacent repos.
    if scale_class == "small":
        if declared_dependencies >= DEP_NUDGE_SMALL or flow_candidates >= FLOW_NUDGE_SMALL:
            scale_class = "medium"
        elif (
            confirmed_profiles >= PROFILE_NUDGE_THRESHOLD
            and _nudge_eligible(source_files, SMALL_MAX_SOURCE_FILES + 1)
        ):
            scale_class = "medium"
    elif scale_class == "medium":
        if declared_dependencies >= DEP_NUDGE_MEDIUM or flow_candidates >= FLOW_NUDGE_MEDIUM:
            scale_class = "large"
        elif (
            confirmed_profiles >= PROFILE_NUDGE_THRESHOLD
            and _nudge_eligible(source_files, MEDIUM_MAX_SOURCE_FILES + 1)
        ):
            scale_class = "large"
    return {
        "class": scale_class,
        "suggested_layout": LAYOUT_BY_CLASS[scale_class],
        "signals": {
            "tracked_files": tracked_files,
            "source_files": source_files,
            "confirmed_profiles": confirmed_profiles,
            "declared_dependencies": declared_dependencies,
            "flow_candidates": flow_candidates,
        },
    }
