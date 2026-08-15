"""Deterministic generation-plan rendering shared by init, preview, and revise.

Plans each manifest document (and each main-priority flow from the flow index)
with a per-document action so a fresh start or revise run shows exactly which
documents will be added, updated, rewritten, or left unchanged before anything
is written. Python and Node emit byte-identical text.
"""

from __future__ import annotations

import json
from pathlib import Path

from runtime.common.python import provenance_store as store
from runtime.common.python.provenance_frontmatter import parse_frontmatter

WRITTEN = {"generated", "needs_review", "complete"}


def flow_is_main_priority(row: dict) -> bool:
    if row.get("priority") == "main":
        return True
    if row.get("priority") == "deferred":
        return False
    if row.get("status") in {"main", "documented"}:
        return True
    if row.get("status") == "placeholder" and row.get("priority") == "main":
        return True
    return False


def document_action(repo: Path, doc: dict, revise: bool = False, storage: str | None = None) -> tuple[str, str]:
    status = doc.get("status", "planned")
    if status == "skipped":
        return "skip", "explicitly skipped"
    if status == "retired":
        return "retired", "out of scope; content moved by retire; entry preserved"
    target = repo / doc["path"]
    if not target.is_file():
        if status in WRITTEN:
            return "add", f"file missing despite {status}"
        return "add", "planned; will be scaffolded"
    if storage is None:
        storage = store.STORAGE_MARKDOWN
    if storage == store.STORAGE_JSON:
        meta = store.read_doc_metadata(repo, doc, storage)
        if meta["state"] == "ok":
            state, provenance = "ok", meta["provenance"]
        elif meta["state"] == "inline":
            return "update", "inline provenance pending sidecar migration"
        elif meta["state"] == "legacy":
            return "rewrite", "legacy provenance pending migration"
        elif meta["state"] == "obsolete":
            return "rewrite", "obsolete provenance schema; run migrate_metadata"
        else:
            return "rewrite", "provenance missing or unparseable"
    else:
        state, provenance, _ = parse_frontmatter(target.read_text(encoding="utf-8", errors="replace"))
        if state == "legacy":
            return "rewrite", "legacy provenance pending migration"
        if state == "obsolete":
            return "rewrite", "obsolete provenance schema; run migrate_metadata"
        if state != "ok" or not isinstance(provenance, dict):
            return "rewrite", "provenance missing or unparseable"
    if status in {"in_progress", "needs_review"}:
        return "rewrite", "status requires re-grounding"
    if status == "planned":
        return "update", "adopts existing file into the plan"
    if status == "generated":
        return "update", "will re-ground changed sections"
    if revise:
        return "unchanged", "fresh; re-check on structural change"
    return "unchanged", "already complete"


def plan_entries(
    repo: Path,
    manifest: dict,
    flow_index_path: Path | None = None,
    revise: bool = False,
) -> list[dict]:
    entries: list[dict] = []
    storage = store.storage_for(manifest)
    for doc in manifest.get("documents", []):
        action, reason = document_action(repo, doc, revise, storage)
        entries.append({
            "id": doc.get("id"),
            "path": doc.get("path"),
            "action": action,
            "reason": reason,
            "flow_id": None,
            "flow_name": None,
            "is_flow": False,
        })
    if flow_index_path is not None and flow_index_path.is_file():
        try:
            index = json.loads(flow_index_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            index = {}
        for row in index.get("flows", []):
            if not flow_is_main_priority(row):
                continue
            flow_id = str(row.get("id") or "")
            slug = str(row.get("slug") or flow_id)
            path = str(row.get("doc_path") or f"docs/flows/{slug}.md")
            doc = next(
                (
                    entry for entry in manifest.get("documents", [])
                    if entry.get("type") == "flow" and entry.get("path") == path
                ),
                None,
            )
            if doc is None:
                action, reason = "add", f"flow {flow_id}: not yet planned"
            else:
                action, reason = document_action(repo, doc, revise, storage)
            entries.append({
                "id": flow_id,
                "path": path,
                "action": action,
                "reason": reason,
                "flow_id": flow_id,
                "flow_name": str(row.get("display_name") or row.get("name") or flow_id),
                "is_flow": True,
            })
    return entries


def plan_lines(
    repo: Path,
    manifest: dict,
    flow_index_path: Path | None = None,
    revise: bool = False,
) -> list[str]:
    docs = [doc for doc in manifest.get("documents", []) if doc.get("status") not in {"skipped", "retired"}]
    project = manifest.get("project", {})
    lines = [f"Generation plan — tier: {project.get('tier', 'unknown')}"]
    profiles = project.get("profiles", {})
    for dimension in ("shapes", "platforms", "frameworks", "concerns", "audiences"):
        values = ", ".join(profiles.get(dimension, [])) or "none"
        lines.append(f"  {dimension}: {values}")
    lines.append("")
    entries = plan_entries(repo, manifest, flow_index_path, revise)
    manifest_entries = [entry for entry in entries if not entry["is_flow"]]
    for entry in manifest_entries:
        lines.append(f"{entry['id']:<28}  {entry['path']}")
        lines.append(f"     action: {entry['action']} — {entry['reason']}")
    flow_entries = [entry for entry in entries if entry["is_flow"]]
    if flow_entries:
        lines.append("")
        lines.append("Flows:")
        for entry in flow_entries:
            label = f"{entry['flow_name']} ({entry['flow_id']})" if entry["flow_id"] else entry["path"]
            lines.append(f"  {label} → {entry['path']}  [{entry['action']}] {entry['reason']}")
    lines.append("")
    flow_count = sum("flow_graph" in doc.get("requires", []) for doc in docs)
    summary = f"{len(docs)} manifest documents; {flow_count} require a flow graph"
    if flow_entries:
        summary += f"; {len(flow_entries)} main-priority flow documents"
    lines.append(summary + ".")
    return lines
