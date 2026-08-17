"""Flow-index schema versioning shared by the flows runtime and metadata
migration.

Both `flow_index` and `migrate_metadata` need the same additive upgrade, so it
lives here in `common` rather than inside the flows runtime. Internal only: no
CLI launcher.
"""

from __future__ import annotations

FLOW_INDEX_VERSION = "1.2"
SUPPORTED_FLOW_INDEX_VERSIONS = ("1.1", "1.2")


def upgrade_index(index: dict) -> dict:
    """Additively upgrade a 1.1 flow index to the current schema.

    Mutates and returns the same dict. Raises ValueError on unsupported
    versions; a current index passes through untouched."""
    version = str(index.get("version") or "1.1")
    if version == FLOW_INDEX_VERSION:
        return index
    if version not in SUPPORTED_FLOW_INDEX_VERSIONS:
        raise ValueError(f"unsupported flow index version: {version}")
    index["version"] = FLOW_INDEX_VERSION
    if index.get("summary") and "written" not in index["summary"]:
        index["summary"]["written"] = sum(
            1
            for row in index.get("flows", [])
            if isinstance(row, dict)
            and row.get("status") == "documented"
            and bool(row.get("summary"))
        )
    return index
