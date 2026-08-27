"""Flow-index schema versioning shared by the flows runtime and metadata
migration.

Both `flow_index` and `migrate_metadata` need the same additive upgrade, so it
lives here in `common` rather than inside the flows runtime. Internal only: no
CLI launcher.
"""

from __future__ import annotations

FLOW_INDEX_VERSION = "1.4"
SUPPORTED_FLOW_INDEX_VERSIONS = ("1.1", "1.2", "1.3", "1.4")


def upgrade_index(index: dict) -> dict:
    """Additively upgrade a 1.1–1.3 flow index to the current schema.

    Mutates and returns the same dict. Raises ValueError on unsupported
    versions; a current index passes through untouched."""
    version = str(index.get("version") or "1.1")
    if version not in SUPPORTED_FLOW_INDEX_VERSIONS:
        raise ValueError(f"unsupported flow index version: {version}")
    if version == "1.1" and index.get("summary") and "written" not in index["summary"]:
        index["summary"]["written"] = sum(
            1
            for row in index.get("flows", [])
            if isinstance(row, dict)
            and row.get("status") == "documented"
            and bool(row.get("summary"))
        )
    if version in {"1.1", "1.2"}:
        for row in index.get("flows", []):
            if not isinstance(row, dict):
                continue
            row.setdefault("parent_flow", None)
            row.setdefault(
                "analysis_state",
                "ready"
                if row.get("status") == "documented" or bool(row.get("written"))
                else "not-analyzed",
            )
    if version in {"1.1", "1.2", "1.3"}:
        for row in index.get("flows", []):
            if not isinstance(row, dict):
                continue
            # 1.4's topology links are optional evidence, never fabricated by
            # migration. Empty values make an upgraded legacy row unambiguous.
            row.setdefault("surface_ref", None)
            row.setdefault("evidence_refs", [])
    index["version"] = FLOW_INDEX_VERSION
    return index
