#!/usr/bin/env python3
"""Three-way project-scale classification shared by intake discovery and
manifest backfill. Not a public CLI.

Classifies a repository `small | medium | large` from one existing walk
(`detect_profiles.inventory`) plus the confirmed-profile count detection
already produces, so no caller re-traverses the tree and no new ignore rules
exist. `suggested_layout` follows the class; a user override is recorded on
the manifest and never re-derived.
"""

from __future__ import annotations

import math
from pathlib import Path

from runtime.catalog.python import detect_profiles

SMALL_MAX_SOURCE_FILES = 15
MEDIUM_MAX_SOURCE_FILES = 200
BOUNDARY_NUDGE_RATIO = 0.20
PROFILE_NUDGE_THRESHOLD = 3

SOURCE_SUFFIXES = {
    ".c", ".cc", ".cpp", ".cs", ".dart", ".go", ".gradle", ".h", ".hpp",
    ".java", ".js", ".jsx", ".kt", ".kts", ".m", ".mm", ".php", ".py", ".rb",
    ".rs", ".sh", ".sol", ".swift", ".ts", ".tsx",
}

LAYOUT_BY_CLASS = {"small": "compact", "medium": "standard", "large": "standard"}


def _nudge_eligible(source_files: int, boundary: int) -> bool:
    """True when `source_files` sits within BOUNDARY_NUDGE_RATIO below a class
    boundary (e.g. 13-15 source files under the small/medium boundary of 16)."""
    return source_files >= math.ceil(boundary * (1 - BOUNDARY_NUDGE_RATIO))


def compute_scale(
    repo: Path,
    files: list[tuple[str, Path]] | None = None,
    detections: list[dict] | None = None,
) -> dict:
    """Pass `files` and/or `detections` when the caller already has them —
    both derive from the same single `inventory(repo)` walk."""
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
    if source_files <= SMALL_MAX_SOURCE_FILES:
        scale_class = "small"
    elif source_files <= MEDIUM_MAX_SOURCE_FILES:
        scale_class = "medium"
    else:
        scale_class = "large"
    if (
        confirmed_profiles >= PROFILE_NUDGE_THRESHOLD
        and scale_class == "small"
        and _nudge_eligible(source_files, SMALL_MAX_SOURCE_FILES + 1)
    ):
        scale_class = "medium"
    elif (
        confirmed_profiles >= PROFILE_NUDGE_THRESHOLD
        and scale_class == "medium"
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
        },
    }
