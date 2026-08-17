#!/usr/bin/env python3
"""Migrate Docforge manifest metadata to 3.9 / provenance 2.0.

Upgrades manifest 3.3 (seeding the project's `unmanaged_docs` list) and
manifest 3.2 / provenance 2.0 (seeding each document's catalog-owned
`description` and the project's `provenance_storage`, then moving inline
frontmatter into `.docforge/provenance/` sidecars when storage is `json`) and
manifest 3.1 / provenance 2.0, plus manifest 3.0 / provenance 1.0 (converting
schema 1.0 and schema-less
legacy frontmatter, including pre-schema `doc` / `graph_snapshot` shapes,
while preserving section evidence), and re-registers any older legacy
manifest — 1.1 (`project_context` / `document_groups`), 2.0 (flat
`documents` with overlay profiles), or any other pre-3.0 shape — as 3.9:
written documents are adopted as `generated` with provenance 2.0, bodies
preserved, and plan entries kept. When a document cannot be converted to
complete provenance 2.0 (missing or unparseable frontmatter, conversion
failure, or incomplete result for a written document), write a best-effort
scaffold, mark the document `in_progress` for agent regeneration, and report
`failed`.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from runtime.common.python._util import dump_json, fail, load_manifest
from runtime.common.python import scale
from runtime.common.python.special_files import SPECIAL_DOC_OUTPUTS
from runtime.common.python import provenance_store as store
from runtime.common.python.provenance_frontmatter import (
    FLOW_VALUES,
    GENERATOR_NAME,
    LEGACY_SCHEMA,
    SCAFFOLD_TOKEN,
    SCHEMA_VERSION,
    SUPPORTED_SCHEMA_VERSIONS,
    migrate_v1_to_v2,
    normalize_sections,
    parse_frontmatter,
    scaffold_provenance,
    split_frontmatter,
)

MANIFEST_CURRENT = "3.9"
MANIFEST_IN_PLACE = ("3.9", "3.8", "3.7", "3.6", "3.5", "3.4", "3.3", "3.2", "3.1", "3.0")
MARKDOWN_EXCEPTIONS = SPECIAL_DOC_OUTPUTS
WRITTEN = {"generated", "needs_review", "complete"}
SCALAR_FIELDS = ("doc_id", "path", "generated_at", "tier", "target_depth")
MANIFEST_LOAD = {
    "allowed_versions": MANIFEST_IN_PLACE,
    "unsupported_hint": "legacy manifests are re-registered by this command",
}
LEGACY_TIER_MAP = {"core": "spine", "standard": "diligence", "extended": "portfolio"}
LEGACY_OVERLAY_MAP = {
    "business-analyst": ("audiences", "business-analysts"),
    "product-owner": ("audiences", "product-owners"),
    "agent-context": ("audiences", "coding-agents"),
    "api": ("shapes", "api-service"),
    "web": ("shapes", "web-app"),
    "library": ("shapes", "library-sdk"),
    "infrastructure": ("shapes", "infrastructure-platform"),
    "data-pipeline": ("shapes", "data-pipeline"),
}
PROFILE_DIMENSIONS = ("shapes", "platforms", "frameworks", "concerns", "audiences")
ORIGIN_KINDS = {
    "tier", "shape", "platform", "framework", "concern", "audience", "condition", "dynamic", "ancestor",
    "compact",
}
STATUSES = {"planned", "in_progress", "generated", "needs_review", "complete", "skipped", "retired"}


def needs_provenance_migration(provenance: dict | None) -> bool:
    if not isinstance(provenance, dict):
        return False
    if "schema" not in provenance:
        return False
    if provenance.get("schema") in SUPPORTED_SCHEMA_VERSIONS and "generator" in provenance and "tool_version" not in provenance:
        return False
    return True


def body_for_rewrite(text: str) -> str:
    raw, body, end = split_frontmatter(text)
    if raw is not None:
        return body
    return text


def migration_defaults(doc: dict, manifest: dict) -> dict:
    project = manifest.get("project", {}) if isinstance(manifest.get("project"), dict) else {}
    embedded = doc.get("provenance") if isinstance(doc.get("provenance"), dict) else {}
    graph = embedded.get("graph") if isinstance(embedded.get("graph"), dict) else {}
    return {
        "doc_id": doc.get("id") or embedded.get("doc_id") or "<DOC_ID>",
        "path": doc.get("path") or embedded.get("path") or embedded.get("doc") or "<DOCUMENT_PATH>",
        "tier": embedded.get("tier") or project.get("tier") or "<TIER>",
        "target_depth": embedded.get("target_depth") or doc.get("target_depth") or "<TARGET_DEPTH>",
        "provider": graph.get("provider") or "<GRAPH_PROVIDER>",
        "flow": graph.get("flow") or "<FLOW_CAPABILITY>",
        "generated_at": embedded.get("generated_at") or "<GENERATED_AT>",
    }


def is_convertible_legacy(provenance: dict | None) -> bool:
    """True when schema-less provenance still carries convertible evidence."""
    if not isinstance(provenance, dict):
        return False
    if "schema" in provenance:
        return False
    if isinstance(provenance.get("sections"), list) and provenance["sections"]:
        return True
    if isinstance(provenance.get("doc"), str) and provenance["doc"]:
        return True
    if isinstance(provenance.get("path"), str) and provenance["path"]:
        return True
    if isinstance(provenance.get("generated_at"), str) and provenance["generated_at"]:
        return True
    return False


def is_scaffold_value(value: object) -> bool:
    return (
        not isinstance(value, str)
        or not value
        or bool(SCAFFOLD_TOKEN.fullmatch(value))
    )


def provenance_gaps(provenance: dict | None) -> list[str]:
    """Return incomplete provenance-2.0 field names for a written document."""
    if not isinstance(provenance, dict):
        return ["provenance"]
    gaps: list[str] = []
    for key in SCALAR_FIELDS:
        if is_scaffold_value(provenance.get(key)):
            gaps.append(key)
    generator = provenance.get("generator")
    if not isinstance(generator, dict):
        gaps.append("generator")
    else:
        for key in ("name", "version"):
            if is_scaffold_value(generator.get(key)):
                gaps.append(f"generator.{key}")
    graph = provenance.get("graph")
    if not isinstance(graph, dict):
        gaps.append("graph")
    else:
        if is_scaffold_value(graph.get("provider")):
            gaps.append("graph.provider")
        flow = graph.get("flow")
        if is_scaffold_value(flow) or flow not in FLOW_VALUES:
            gaps.append("graph.flow")
    sections = provenance.get("sections")
    if not isinstance(sections, list) or not sections:
        gaps.append("sections")
    elif not any(
        isinstance(section, dict)
        and isinstance(section.get("sources"), list)
        and section["sources"]
        for section in sections
    ):
        gaps.append("section sources")
    return gaps


def mark_for_agent_regen(doc: dict) -> bool:
    """Demote a written document so the agent regenerates provenance.

    Returns True when status changed to in_progress.
    """
    previous = doc.get("status")
    if previous not in WRITTEN:
        return False
    doc["status"] = "in_progress"
    doc["audit"] = None
    return True


def provenance_from_manifest(doc: dict, manifest: dict) -> dict:
    defaults = migration_defaults(doc, manifest)
    embedded = doc.get("provenance") if isinstance(doc.get("provenance"), dict) else {}
    generated = scaffold_provenance(
        str(defaults["doc_id"]),
        str(defaults["path"]),
        tier=str(defaults["tier"]),
        target_depth=str(defaults["target_depth"]),
        provider=str(defaults["provider"]),
        flow=str(defaults["flow"]),
        generated_at=str(defaults["generated_at"]),
    )
    if isinstance(embedded.get("sections"), list) and embedded["sections"]:
        try:
            return migrate_v1_to_v2(embedded, defaults=defaults)
        except Exception:
            pass
    elif is_convertible_legacy(embedded):
        try:
            return migrate_v1_to_v2(embedded, defaults=defaults)
        except Exception:
            pass
    return generated


def _public_for(text: str, doc: dict) -> dict:
    """Public identity from inline frontmatter, falling back to the manifest."""
    state, data = store.read_inline(text)
    public: dict = {}
    if state == "ok":
        for key in ("id", "title", "description"):
            if isinstance(data.get(key), str) and data[key]:
                public[key] = data[key]
    for key in ("id", "title", "description"):
        if not public.get(key) and doc.get(key):
            public[key] = doc[key]
    if not public.get("id"):
        public["id"] = doc.get("id", "")
    if not public.get("title"):
        public["title"] = doc.get("id", "document").replace("-", " ").title()
    return public


def _write_output(
    repo: Path,
    doc: dict,
    text: str,
    provenance: dict,
    dry_run: bool,
) -> None:
    """Persist provenance to the folder sidecar and leave the markdown clean.

    Stripping is unconditional: this is the one pass that guarantees no
    generated document keeps a frontmatter block."""
    if dry_run:
        return
    body = body_for_rewrite(text)
    entry = _public_for(text, doc)
    entry["provenance"] = provenance
    store.write_entry(repo, doc["path"], entry)
    (repo / doc["path"]).write_text(body.lstrip("\n"), encoding="utf-8")


def fail_document(
    repo: Path,
    doc: dict,
    manifest: dict,
    dry_run: bool,
    reason: str,
    *,
    provenance: dict | None = None,
    text: str | None = None,
) -> dict:
    """Write best-effort provenance and mark written docs for agent regen."""
    path = repo / doc["path"]
    if text is None:
        text = path.read_text(encoding="utf-8", errors="replace")
    generated = provenance if isinstance(provenance, dict) else provenance_from_manifest(doc, manifest)
    demoted = mark_for_agent_regen(doc)
    detail = f"{reason}; agent must regenerate provenance"
    if demoted:
        detail += "; status -> in_progress"
    result = {
        "doc": doc["path"],
        "action": "failed",
        "detail": detail,
    }
    _write_output(repo, doc, text, generated, dry_run)
    doc["provenance"] = generated
    return result


def regenerate_planned(
    repo: Path,
    doc: dict,
    manifest: dict,
    dry_run: bool,
    reason: str,
    text: str,
) -> dict:
    """Scaffold-only rewrite for non-written documents (no failure demotion)."""
    generated = provenance_from_manifest(doc, manifest)
    result = {
        "doc": doc["path"],
        "action": "regenerate",
        "detail": f"{reason}; wrote provenance {SCHEMA_VERSION} scaffold from manifest",
    }
    _write_output(repo, doc, text, generated, dry_run)
    doc["provenance"] = generated
    return result


def write_migrated(
    repo: Path,
    doc: dict,
    manifest: dict,
    text: str,
    migrated: dict,
    dry_run: bool,
    detail: str,
    *,
    require_complete: bool,
) -> dict:
    gaps = provenance_gaps(migrated) if require_complete else []
    if gaps:
        return fail_document(
            repo,
            doc,
            manifest,
            dry_run,
            f"{detail}; incomplete after conversion ({', '.join(gaps)})",
            provenance=migrated,
            text=text,
        )
    result = {"doc": doc["path"], "action": "migrate", "detail": detail}
    _write_output(repo, doc, text, migrated, dry_run)
    doc["provenance"] = migrated
    return result


def migrate_document_file(
    repo: Path,
    doc: dict,
    manifest: dict,
    dry_run: bool,
    *,
    require_complete: bool | None = None,
) -> dict:
    path = repo / doc["path"]
    result = {"doc": doc["path"], "action": "skip", "detail": ""}
    if doc.get("provenance_mode") == "manifest" or path.name in MARKDOWN_EXCEPTIONS:
        result["detail"] = "manifest-only provenance"
        return result
    if not path.is_file() or path.suffix.lower() != ".md":
        result["action"] = "missing"
        result["detail"] = "file absent"
        return result
    must_complete = (
        require_complete
        if require_complete is not None
        else doc.get("status") in WRITTEN
    )
    entry = store.entry_for(repo, doc["path"])
    if isinstance(entry, dict) and isinstance(entry.get("provenance"), dict):
        provenance = entry["provenance"]
        defaults = migration_defaults(doc, manifest)
        if needs_provenance_migration(provenance):
            try:
                migrated = migrate_v1_to_v2(provenance, defaults=defaults)
            except Exception:
                migrated = provenance_from_manifest(doc, manifest)
            if not dry_run:
                updated = dict(entry)
                updated["provenance"] = migrated
                store.write_entry(repo, doc["path"], updated)
            doc["provenance"] = migrated
            return {"doc": doc["path"], "action": "migrate", "detail": f"sidecar schema -> {SCHEMA_VERSION}"}
        if must_complete:
            gaps = provenance_gaps(provenance)
            if gaps:
                demoted = mark_for_agent_regen(doc)
                detail = f"incomplete provenance 2.0 ({', '.join(gaps)}); agent must regenerate provenance"
                if demoted:
                    detail += "; status -> in_progress"
                doc["provenance"] = provenance
                return {"doc": doc["path"], "action": "failed", "detail": detail}
        doc["provenance"] = provenance
        result["detail"] = f"already sidecar schema {provenance.get('schema')}"
        return result
    text = path.read_text(encoding="utf-8", errors="replace")
    state, provenance, _end = parse_frontmatter(text)
    defaults = migration_defaults(doc, manifest)
    if state in {"missing", "unparseable"}:
        reasons = {
            "missing": "missing provenance",
            "unparseable": "unparseable provenance",
        }
        if must_complete:
            return fail_document(repo, doc, manifest, dry_run, reasons[state], text=text)
        return regenerate_planned(repo, doc, manifest, dry_run, reasons[state], text)
    if state == "legacy" and isinstance(provenance, dict):
        if is_convertible_legacy(provenance):
            _raw, body, _ = split_frontmatter(text)
            try:
                migrated = migrate_v1_to_v2(provenance, body, defaults=defaults)
            except Exception as exc:
                return fail_document(
                    repo, doc, manifest, dry_run,
                    f"legacy conversion failed: {exc}", text=text,
                )
            return write_migrated(
                repo, doc, manifest, text, migrated, dry_run,
                f"legacy schema-less -> {SCHEMA_VERSION}",
                require_complete=must_complete,
            )
        if must_complete:
            return fail_document(
                repo, doc, manifest, dry_run, "legacy provenance without schema", text=text,
            )
        return regenerate_planned(
            repo, doc, manifest, dry_run, "legacy provenance without schema", text,
        )
    if state == "ok" and not needs_provenance_migration(provenance):
        if must_complete:
            gaps = provenance_gaps(provenance)
            if gaps:
                return fail_document(
                    repo, doc, manifest, dry_run,
                    f"incomplete provenance 2.0 ({', '.join(gaps)})",
                    provenance=provenance,
                    text=text,
                )
        doc["provenance"] = provenance
        if dry_run:
            return {"doc": doc["path"], "action": "migrate", "detail": "inline -> sidecar"}
        action = store.move_inline_to_sidecar(repo, doc)
        return {
            "doc": doc["path"],
            "action": "migrate" if action == "moved" else "skip",
            "detail": "inline -> sidecar" if action == "moved" else action,
        }
    if state not in {"ok", "obsolete"} or not isinstance(provenance, dict):
        if must_complete:
            return fail_document(
                repo, doc, manifest, dry_run, f"unsupported state {state}", text=text,
            )
        return regenerate_planned(
            repo, doc, manifest, dry_run, f"unsupported state {state}", text,
        )
    if provenance.get("schema") not in (SUPPORTED_SCHEMA_VERSIONS | {LEGACY_SCHEMA}) and "tool_version" not in provenance:
        reason = f"unsupported schema {provenance.get('schema')}"
        if must_complete:
            return fail_document(repo, doc, manifest, dry_run, reason, text=text)
        return regenerate_planned(repo, doc, manifest, dry_run, reason, text)
    _raw, body, _ = split_frontmatter(text)
    try:
        migrated = migrate_v1_to_v2(provenance, body, defaults=defaults)
    except Exception as exc:
        return fail_document(
            repo, doc, manifest, dry_run, f"conversion failed: {exc}", text=text,
        )
    return write_migrated(
        repo, doc, manifest, text, migrated, dry_run,
        f"schema {provenance.get('schema')} -> {SCHEMA_VERSION}",
        require_complete=must_complete,
    )


def seed_descriptions(
    docs: list[dict],
    by_id: dict[str, dict],
    by_type: dict[str, list[dict]],
    by_path: dict[str, dict],
) -> list[str]:
    """Seed catalog-owned `description` (the catalog `summary`) on documents
    that lack one; existing values are never overwritten."""
    seeded: list[str] = []
    for doc in docs:
        if doc.get("description"):
            continue
        definition = match_definition(
            by_id,
            by_type,
            by_path,
            str(doc.get("id") or ""),
            doc.get("type"),
            str(doc.get("path") or ""),
        )
        summary = (definition or {}).get("summary")
        if isinstance(summary, str) and summary:
            doc["description"] = summary
            seeded.append(str(doc.get("id") or ""))
    return seeded


def backfill_project_scale(repo: Path, tier: str = "diligence") -> dict:
    """Scale record for a legacy manifest with no scale field.

    Legacy repositories were written before layout existed, at standard
    paths — migration must never silently fold them to compact, so the
    backfilled layout is always `standard` with `decided_by: "migration"`.
    The `class` still comes from live detection, and `detected_layout`
    records what detection would have said so a later revise can show the
    drift. A present `project.scale` is never overwritten."""
    detected = scale.compute_scale(repo)
    record = {
        "class": detected["class"],
        "layout": "standard",
        "decided_by": "migration",
        "decided_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "signals": detected["signals"],
    }
    if detected["suggested_layout"] != "standard":
        record["detected_layout"] = detected["suggested_layout"]
    return record


def migrate_flow_index(repo: Path, dry_run: bool) -> dict | None:
    """Upgrade a 1.1 flow index to 1.2 as part of metadata migration.

    One bare revise leaves every metadata artifact at the newest schema —
    manifest, provenance sidecars, and now the flow ledger. The upgrade is
    the same additive merge `flow_index` performs on load (version bump plus
    the `summary.written` count); an absent, unparseable, or already-current
    index is skipped silently."""
    from runtime.common.python.flow_index_schema import (
        FLOW_INDEX_VERSION,
        SUPPORTED_FLOW_INDEX_VERSIONS,
        upgrade_index,
    )

    path = repo / ".docforge" / "flow-index.json"
    if not path.is_file():
        return None
    try:
        index = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(index, dict):
        return None
    version = str(index.get("version") or "1.1")
    if version == FLOW_INDEX_VERSION:
        return None
    if version not in SUPPORTED_FLOW_INDEX_VERSIONS:
        return None
    if not dry_run:
        upgrade_index(index)
        path.write_text(json.dumps(index, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return {
        "doc": ".docforge/flow-index.json",
        "action": "migrate",
        "detail": f"flow index version -> {FLOW_INDEX_VERSION}",
    }


def constrain_scale_layout(project: dict) -> bool:
    """Force a portfolio manifest off compact. Compact covers spine and
    diligence only, so a manifest written before that rule (or hand-edited)
    is corrected here rather than left generating a folded portfolio layer."""
    record = project.get("scale")
    if not isinstance(record, dict) or record.get("layout") != "compact":
        return False
    layout, decided_by = scale.layout_for(
        project.get("tier", "diligence"), "compact", explicit=False
    )
    if layout == "compact":
        return False
    record.setdefault("detected_class", record.get("class"))
    record["layout"] = layout
    record["decided_by"] = decided_by
    return True


def migrate_agent_context_3_9(manifest: dict) -> bool:
    """Drop mode state and pin retained agent documents to catalog metadata.

    `agents_index` is deliberately excluded from canonicalization and demotion:
    when it has written content, keeping its manifest entry and status is what
    lets the normal reconcile/retire workflow treat it as a retirement
    candidate without touching its body.
    """
    from runtime.catalog.python import query_catalog

    changed = False
    project = manifest.get("project")
    if isinstance(project, dict) and "agent_context" in project:
        project.pop("agent_context")
        changed = True

    docs = manifest.get("documents")
    if not isinstance(docs, list):
        return changed

    for doc in docs:
        members = doc.get("compact_members")
        if isinstance(members, list):
            retained = [
                member for member in members
                if (member.get("id") if isinstance(member, dict) else member) != "agents_index"
            ]
            if retained != members:
                doc["compact_members"] = retained
                changed = True

    agent_docs = [
        doc for doc in docs
        if doc.get("group") == "agent-context" and doc.get("id") != "agents_index"
    ]
    if not agent_docs:
        return changed

    by_id, by_type, by_path = load_catalog_maps()
    audiences = (
        project.get("profiles", {}).get("audiences", [])
        if isinstance(project, dict)
        else []
    )
    for doc in agent_docs:
        definition = match_definition(
            by_id,
            by_type,
            by_path,
            str(doc.get("id") or ""),
            doc.get("type"),
            str(doc.get("path") or ""),
        )
        if definition is None:
            continue
        canonical = {
            "scaffold_template": definition["template_file"],
            "instruction_file": definition.get("instruction_file"),
            "requires": list(definition.get("requires", [])),
        }
        primary, presentation, _ = query_catalog.resolve_presentation(definition, audiences)
        canonical["presentation"] = {"primary_audience": primary, **presentation}
        for field, value in canonical.items():
            if doc.get(field) != value:
                doc[field] = value
                changed = True
        if "presentation_override" in doc:
            doc.pop("presentation_override")
            changed = True
        if doc.get("status") in WRITTEN:
            doc["status"] = "in_progress"
            doc["audit"] = None
            changed = True
    return changed


def migrate_manifest_object(
    manifest: dict,
    repo: Path,
    *,
    demote_incomplete: bool = False,
) -> bool:
    changed = False
    upgraded_version = False
    source_version = manifest.get("version")
    if source_version in set(MANIFEST_IN_PLACE) - {MANIFEST_CURRENT}:
        manifest["version"] = MANIFEST_CURRENT
        changed = True
        upgraded_version = True
    project = manifest.get("project")
    # `markdown` storage is gone: normalize the field, and the per-document
    # pass below strips whatever frontmatter that mode left behind.
    if isinstance(project, dict) and project.get("provenance_storage") != store.STORAGE_JSON:
        project["provenance_storage"] = store.STORAGE_JSON
        changed = True
    if isinstance(project, dict) and not isinstance(project.get("unmanaged_docs"), list):
        project["unmanaged_docs"] = []
        changed = True
    if isinstance(project, dict) and not isinstance(project.get("scale"), dict):
        project["scale"] = backfill_project_scale(repo, project.get("tier", "diligence"))
        changed = True
    if isinstance(project, dict) and constrain_scale_layout(project):
        changed = True
    if upgraded_version and migrate_agent_context_3_9(manifest):
        changed = True
    # Schema 3.7 added two measurement signals. Refresh them on any upgrade —
    # signals are measurements; class/layout/decided_by (possible user
    # decisions) are never re-derived.
    scale_record = project.get("scale") if isinstance(project, dict) else None
    if upgraded_version and isinstance(scale_record, dict):
        signals = scale_record.get("signals")
        if not isinstance(signals, dict) or (
            "declared_dependencies" not in signals or "flow_candidates" not in signals
        ):
            scale_record["signals"] = scale.compute_scale(repo)["signals"]
            changed = True
    docs = manifest.get("documents", [])
    if any(not doc.get("description") for doc in docs):
        by_id, by_type, by_path = load_catalog_maps()
        if seed_descriptions(docs, by_id, by_type, by_path):
            changed = True
    for doc in docs:
        provenance = doc.get("provenance")
        defaults = migration_defaults(doc, manifest)
        if needs_provenance_migration(provenance):
            try:
                doc["provenance"] = migrate_v1_to_v2(provenance, defaults=defaults)
            except Exception:
                doc["provenance"] = provenance_from_manifest(doc, manifest)
            changed = True
        elif is_convertible_legacy(provenance):
            try:
                doc["provenance"] = migrate_v1_to_v2(provenance, defaults=defaults)
            except Exception:
                doc["provenance"] = provenance_from_manifest(doc, manifest)
            changed = True
        elif not isinstance(provenance, dict) or not provenance:
            doc["provenance"] = provenance_from_manifest(doc, manifest)
            changed = True
        if demote_incomplete and doc.get("status") in WRITTEN and provenance_gaps(doc.get("provenance")):
            if mark_for_agent_regen(doc):
                changed = True
    return changed


def migrate(repo: Path, manifest_path: Path, dry_run: bool) -> tuple[list[dict], bool]:
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"manifest must be a JSON object: {manifest_path}")
    version = data.get("version")
    if version not in set(MANIFEST_IN_PLACE):
        return migrate_legacy(repo, manifest_path, data, dry_run)
    manifest = load_manifest(manifest_path, **MANIFEST_LOAD)
    reports: list[dict] = []
    retirement_candidates = [
        str(doc.get("id"))
        for doc in manifest.get("documents", [])
        if version != MANIFEST_CURRENT
        and doc.get("id") == "agents_index"
        and doc.get("status") in WRITTEN
    ]
    # Snapshot written status before any demotion so file conversion can still
    # require complete provenance 2.0 for previously published documents.
    require_complete = {
        doc["id"]: doc.get("status") in WRITTEN
        for doc in manifest.get("documents", [])
        if isinstance(doc.get("id"), str)
    }
    object_changed = migrate_manifest_object(manifest, repo, demote_incomplete=False)
    try:
        manifest_label = str(manifest_path.relative_to(repo))
    except ValueError:
        manifest_label = str(manifest_path)
    if object_changed:
        candidate_detail = ""
        if retirement_candidates:
            candidate_detail = (
                "; retained as retirement candidate without touching its body: "
                + ", ".join(sorted(retirement_candidates))
            )
        reports.append({
            "doc": manifest_label,
            "action": "migrate",
            "detail": (
                f"manifest version -> {MANIFEST_CURRENT}; provenance objects normalized"
                f"{candidate_detail}"
            ),
        })
    else:
        reports.append({
            "doc": manifest_label,
            "action": "skip",
            "detail": f"manifest already {manifest.get('version')}",
        })
    for doc in manifest.get("documents", []):
        reports.append(
            migrate_document_file(
                repo,
                doc,
                manifest,
                dry_run,
                require_complete=require_complete.get(doc.get("id"), doc.get("status") in WRITTEN),
            )
        )
    if not dry_run:
        migrate_manifest_object(manifest, repo, demote_incomplete=True)
        manifest_path.write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    flow_index_report = migrate_flow_index(repo, dry_run)
    if flow_index_report is not None:
        reports.append(flow_index_report)
    changed = any(
        item["action"] in {"migrate", "regenerate", "failed"} for item in reports
    )
    return reports, changed


def ensure_migrated(repo: Path, manifest_path: Path) -> dict:
    """Migrate in place and return the loaded current manifest."""
    migrate(repo, manifest_path, dry_run=False)
    return load_manifest(manifest_path, **MANIFEST_LOAD)


# ---------------------------------------------------------------------------
# Legacy manifest re-registration (any pre-3.0 version)
# ---------------------------------------------------------------------------


def legacy_profiles(overlays: list[str]) -> dict[str, list[str]]:
    """Map legacy overlays onto the typed profile dimensions.

    A legacy manifest with no audience-mapping overlay keeps the 3.x init
    default audience (engineers + beginners)."""
    profiles = {dimension: [] for dimension in PROFILE_DIMENSIONS}
    for overlay in overlays:
        mapping = LEGACY_OVERLAY_MAP.get(overlay)
        if mapping is not None:
            dimension, profile_id = mapping
            if profile_id not in profiles[dimension]:
                profiles[dimension].append(profile_id)
    if not profiles["audiences"]:
        profiles["audiences"] = ["engineers", "beginners"]
    return profiles


def legacy_project(manifest: dict, repo: Path) -> dict:
    """Best-effort 3.1 project block from any legacy manifest shape.

    Reads either `project_context` (1.x) or `project` (2.x), maps legacy
    tiers (`core` / `standard` / `extended`) and overlays, and accepts a
    pre-existing `project.profiles` when present."""
    ctx = manifest.get("project_context")
    proj = manifest.get("project")
    base = ctx if isinstance(ctx, dict) else (proj if isinstance(proj, dict) else {})
    tier = base.get("tier")
    if tier in LEGACY_TIER_MAP:
        tier = LEGACY_TIER_MAP[tier]
    if tier not in {"spine", "diligence", "portfolio"}:
        tier = "spine"
    overlays = base.get("overlays")
    if not isinstance(overlays, list):
        overlays = []
    profiles = legacy_profiles(overlays)
    if isinstance(proj, dict) and isinstance(proj.get("profiles"), dict):
        existing = proj["profiles"]
        merged = {
            dimension: [str(value) for value in existing.get(dimension) or []]
            for dimension in PROFILE_DIMENSIONS
        }
        if not merged["audiences"]:
            merged["audiences"] = profiles["audiences"]
        profiles = merged
    name = ""
    if isinstance(ctx, dict):
        name = ctx.get("repo_name") or ""
    name = name or (proj.get("name") if isinstance(proj, dict) else None) or repo.name
    return {
        "tier": tier,
        "profiles": profiles,
        "name": name,
        "root": str(repo.resolve()),
    }


def legacy_documents(manifest: dict) -> list[tuple[dict, str]]:
    """Flatten any legacy manifest shape into (doc, group) records.

    Handles the 1.x `document_groups` container and the 2.x+ flat
    `documents` array; anything else yields no documents."""
    out: list[tuple[dict, str]] = []
    groups = manifest.get("document_groups")
    if isinstance(groups, list):
        for group_obj in groups:
            group = group_obj.get("group") if isinstance(group_obj, dict) else None
            docs = group_obj.get("documents") if isinstance(group_obj, dict) else None
            for doc in docs or []:
                if isinstance(doc, dict):
                    out.append((doc, group or "reference"))
        return out
    docs = manifest.get("documents")
    if isinstance(docs, list):
        for doc in docs:
            if isinstance(doc, dict):
                out.append((doc, doc.get("group") or "reference"))
    return out


def legacy_sections(doc: dict) -> list:
    """Section evidence from either the 1.x `doc.sections` or the 2.x
    `doc.provenance.sections` shape."""
    sections = doc.get("sections")
    if isinstance(sections, list):
        return sections
    provenance = doc.get("provenance")
    if isinstance(provenance, dict):
        nested = provenance.get("sections")
        if isinstance(nested, list):
            return nested
    return []


def legacy_embedded_provenance(doc: dict) -> dict | None:
    """A manifest-embedded provenance that is already schema 2.0 (2.x-era
    manifests with a provenance object carrying a schema)."""
    provenance = doc.get("provenance")
    if (
        isinstance(provenance, dict)
        and provenance.get("schema") in SUPPORTED_SCHEMA_VERSIONS
        and isinstance(provenance.get("doc_id"), str)
    ):
        return provenance
    return None


def normalize_legacy_origins(origins: list) -> list[dict]:
    """Normalize legacy selection origins to the 3.1 origin kinds.

    2.x-era `overlay` origins map through the overlay table to their profile
    dimension; unknown origins are dropped so the migrated manifest stays
    schema-valid."""
    out: list[dict] = []
    for origin in origins or []:
        if not isinstance(origin, dict):
            continue
        kind = origin.get("kind")
        origin_id = origin.get("id")
        if kind == "overlay":
            mapping = LEGACY_OVERLAY_MAP.get(origin_id)
            if mapping is None:
                continue
            dimension, profile_id = mapping
            out.append({"kind": "shape" if dimension == "shapes" else "audience", "id": profile_id})
            continue
        if kind in ORIGIN_KINDS and isinstance(origin_id, str):
            out.append({"kind": kind, "id": origin_id})
    return out


def load_catalog_maps() -> tuple[dict, dict, dict]:
    from runtime.catalog.python import query_catalog

    by_id: dict[str, dict] = {}
    by_type: dict[str, list[dict]] = {}
    by_path: dict[str, dict] = {}
    for row in query_catalog.load_index()["document_types"]:
        detail = query_catalog.load_type(row["id"])
        by_id[detail["id"]] = detail
        by_type.setdefault(detail.get("type"), []).append(detail)
        if detail.get("path"):
            by_path[detail["path"]] = detail
    return by_id, by_type, by_path


def match_definition(
    by_id: dict,
    by_type: dict,
    by_path: dict,
    doc_id: str,
    legacy_type: str | None,
    path: str,
) -> dict | None:
    """Match a legacy document to a current catalog definition: by id, then by
    a unique type, then by an exact catalog path. Returns None for removed or
    renamed types so the document is adopted generically."""
    if doc_id in by_id:
        return by_id[doc_id]
    candidates = by_type.get(legacy_type) or []
    if len(candidates) == 1:
        return candidates[0]
    return by_path.get(path)


def probe_code_graph(repo: Path) -> dict[str, str]:
    """Read-only detection of a ready code-graph artifact, so adopted written
    documents get a concrete graph provider (schema 2.0 requires one)."""
    if (repo / ".ua").is_dir() or (repo / ".ua" / "knowledge-graph.json").is_file():
        return {"provider": "understand-anything", "flow": "native"}
    if (repo / ".gitnexus").is_dir():
        return {"provider": "gitnexus", "flow": "native"}
    if (repo / ".codegraph").is_dir():
        return {"provider": "codegraph", "flow": "none"}
    return {"provider": "none", "flow": "none"}


def provenance_from_legacy_sections(
    sections: list,
    doc_id: str,
    path: str,
    generated_at: str,
    tier: str,
    graph: dict[str, str],
    target_depth: str,
    version: str,
) -> dict:
    normalized = normalize_sections(
        [
            {"id": section.get("id"), "sources": section.get("sources")}
            for section in sections
            if isinstance(section, dict)
        ]
    )
    return {
        "schema": SCHEMA_VERSION,
        "doc_id": doc_id,
        "path": path,
        "generated_at": generated_at,
        "generator": {"name": GENERATOR_NAME, "version": version},
        "tier": tier,
        "target_depth": target_depth,
        "graph": {"provider": graph["provider"], "flow": graph["flow"]},
        "sections": normalized,
    }


def provenance_for_legacy_file(
    repo: Path,
    doc_id: str,
    path: str,
    sections: list,
    graph: dict[str, str],
    generated_at: str,
    tier: str,
    target_depth: str,
    version: str,
    embedded: dict | None = None,
) -> tuple[dict, str, bool]:
    """Best provenance 2.0 for a written legacy document.

    Returns (provenance, detail, needs_rewrite): the file's own frontmatter
    wins when present; otherwise an already-schema-2.0 manifest provenance;
    otherwise the manifest's aggregated sections are converted; otherwise a
    scaffold is emitted (detail names the reason)."""
    text = (repo / path).read_text(encoding="utf-8", errors="replace")
    state, embedded_file, _end = parse_frontmatter(text)
    defaults = {
        "doc_id": doc_id,
        "path": path,
        "generated_at": generated_at,
        "tier": tier,
        "target_depth": target_depth,
    }
    if state == "ok" and isinstance(embedded_file, dict):
        return embedded_file, f"already schema {embedded_file.get('schema')}", False
    if state in {"legacy", "obsolete"} and isinstance(embedded_file, dict):
        try:
            migrated = migrate_v1_to_v2(embedded_file, body_for_rewrite(text), defaults=defaults)
            return migrated, f"frontmatter migrated to schema {SCHEMA_VERSION}", True
        except Exception as exc:  # noqa: BLE001 - best-effort conversion
            fallback = provenance_from_legacy_sections(
                sections, doc_id, path, generated_at, tier, graph, target_depth, version
            )
            return (
                dict(embedded, sections=normalize_sections(embedded.get("sections")))
                if embedded is not None
                else fallback,
                f"frontmatter conversion failed ({exc}); provenance from manifest",
                True,
            )
    if state == "unparseable":
        return (
            dict(embedded, sections=normalize_sections(embedded.get("sections")))
            if embedded is not None
            else provenance_from_legacy_sections(
                sections, doc_id, path, generated_at, tier, graph, target_depth, version
            ),
            "frontmatter unparseable; provenance from manifest",
            True,
        )
    if embedded is not None:
        return (
            dict(embedded, sections=normalize_sections(embedded.get("sections"))),
            "provenance 2.0 carried from manifest",
            True,
        )
    if sections:
        return (
            provenance_from_legacy_sections(
                sections, doc_id, path, generated_at, tier, graph, target_depth, version
            ),
            "provenance from manifest sections",
            True,
        )
    return (
        scaffold_provenance(
            doc_id,
            path,
            tier=tier,
            target_depth=target_depth,
            provider=graph["provider"],
            flow=graph["flow"],
            generated_at=generated_at,
        ),
        "no provenance evidence; scaffolded",
        True,
    )


def build_legacy_entry(
    definition: dict | None,
    legacy_doc: dict,
    path: str,
    group: str,
    status: str,
    provenance: dict | None,
    generated_at: str,
    tier: str,
    write_order: int,
    version: str,
) -> dict:
    """Build a 3.1 document entry from a legacy document.

    The legacy document's own 3.x-compatible fields are preserved when
    present; missing fields fall back to the catalog definition, then to
    defaults, so 2.x-era manifests keep their metadata while 1.x-era entries
    gain catalog-owned structure."""
    id_value = str(legacy_doc.get("id") or "")
    provenance_mode = legacy_doc.get("provenance_mode")
    if provenance_mode not in {"sections", "manifest"}:
        provenance_mode = "manifest" if path in MARKDOWN_EXCEPTIONS else "sections"
    target_depth = (
        legacy_doc.get("target_depth")
        or (definition or {}).get("target_depth")
        or "orientation"
    )
    selection = legacy_doc.get("selection")
    if not isinstance(selection, dict):
        selection = {}
    origins = normalize_legacy_origins(selection.get("origins"))
    if not origins:
        origins = [{"kind": "dynamic", "id": f"legacy-v{version}"}]
    evidence = selection.get("evidence")
    requires = legacy_doc.get("requires")
    if not isinstance(requires, list):
        requires = list((definition or {}).get("requires") or [])
    write_order_value = legacy_doc.get("write_order")
    if not isinstance(write_order_value, int):
        write_order_value = (definition or {}).get("write_order") or write_order
    base = {
        "id": id_value,
        "title": (
            legacy_doc.get("title")
            or (definition or {}).get("title")
            or id_value.replace("_", " ").replace("-", " ").title()
        ),
        "path": path,
        "group": group,
        "selection": {"origins": origins, "evidence": evidence if isinstance(evidence, list) else []},
        "status": status,
        "requires": requires,
        "scaffold_template": (
            legacy_doc.get("scaffold_template")
            or legacy_doc.get("template")
            or (definition or {}).get("template_file")
            or "generic.md"
        ),
        "instruction_file": (
            legacy_doc["instruction_file"]
            if "instruction_file" in legacy_doc
            else (definition or {}).get("instruction_file")
        ),
        "target_depth": target_depth,
        "write_order": write_order_value,
        "provenance_mode": provenance_mode,
        "audit_profile": (
            legacy_doc.get("audit_profile")
            or (definition or {}).get("audit_profile")
            or "standard"
        ),
        "provenance": provenance
        or scaffold_provenance(
            id_value,
            path,
            tier=tier,
            target_depth=target_depth,
            generated_at=generated_at,
        ),
        "audit": None,
    }
    if "type" in legacy_doc and legacy_doc.get("type"):
        base["type"] = legacy_doc["type"]
    elif definition is not None:
        base["type"] = definition.get("type") or "generic"
    else:
        base["type"] = "generic"
    contract_revision = legacy_doc.get("contract_revision") or (
        (definition or {}).get("contract_revision")
    )
    if contract_revision:
        base["contract_revision"] = contract_revision
    return base


def migrate_legacy(
    repo: Path,
    manifest_path: Path,
    manifest: dict,
    dry_run: bool,
) -> tuple[list[dict], bool]:
    """Re-register any pre-3.0 legacy manifest as 3.1.

    The manifest's own version drives the generator stamp and origin label —
    nothing is hard-coded to one legacy version. Written documents whose
    files exist are adopted as `generated` (never `complete` — no
    independent audit survived) with provenance 2.0; bodies and source
    hashes are preserved, and legacy frontmatter is migrated to schema 2.0.
    Unmatched types are adopted generically. Skipped documents stay skipped;
    written documents with a missing file are reported failed and demoted to
    `planned` for regeneration."""
    version = str(manifest.get("version") or "unknown")
    reports: list[dict] = []
    by_id, by_type, by_path = load_catalog_maps()
    project = legacy_project(manifest, repo)
    generated_at = manifest.get("generated_at") or datetime.now(timezone.utc).isoformat()
    graph = probe_code_graph(repo)
    new_manifest = {
        "version": MANIFEST_CURRENT,
        "generated_at": generated_at,
        "project": {
            "name": project["name"],
            "root": project["root"],
            "tier": project["tier"],
            "scale": backfill_project_scale(repo, project["tier"]),
            "profiles": project["profiles"],
            "provenance_storage": store.STORAGE_JSON,
            "unmanaged_docs": [],
        },
        "discovery": [],
        "discovery_gate": None,
        "documents": [],
        "metadata": {},
    }
    adopted = 0
    kept_planned = 0
    skipped = 0
    failed = 0
    fallback = 0
    write_order = 1000
    for legacy_doc, group in legacy_documents(manifest):
        doc_id = str(legacy_doc.get("id") or "")
        path = str(legacy_doc.get("path") or "")
        legacy_status = legacy_doc.get("status") or "planned"
        if legacy_status not in STATUSES:
            legacy_status = "planned"
        sections = legacy_sections(legacy_doc)
        embedded = legacy_embedded_provenance(legacy_doc)
        definition = match_definition(
            by_id, by_type, by_path, doc_id, legacy_doc.get("type"), path
        )
        write_order += 1
        if legacy_status == "skipped":
            new_manifest["documents"].append(
                build_legacy_entry(
                    definition, legacy_doc, path, group, "skipped",
                    None, generated_at, project["tier"], write_order, version,
                )
            )
            skipped += 1
            reports.append({"doc": path, "action": "skip", "detail": "kept skipped"})
            continue
        if not path or not (repo / path).is_file():
            if legacy_status in WRITTEN:
                failed += 1
                reports.append(
                    {"doc": path, "action": "failed", "detail": "file absent; agent must regenerate"}
                )
            new_manifest["documents"].append(
                build_legacy_entry(
                    definition, legacy_doc, path, group, "planned",
                    None, generated_at, project["tier"], write_order, version,
                )
            )
            kept_planned += 1
            continue
        if legacy_status not in WRITTEN:
            new_manifest["documents"].append(
                build_legacy_entry(
                    definition, legacy_doc, path, group, legacy_status,
                    None, generated_at, project["tier"], write_order, version,
                )
            )
            kept_planned += 1
            reports.append({"doc": path, "action": "migrate", "detail": f"kept {legacy_status}"})
            continue
        target_depth = (
            legacy_doc.get("target_depth")
            or (definition or {}).get("target_depth")
            or "orientation"
        )
        provenance, detail, needs_rewrite = provenance_for_legacy_file(
            repo, doc_id, path, sections, graph, generated_at,
            project["tier"], target_depth, version, embedded=embedded,
        )
        status = "generated" if legacy_status == "complete" else legacy_status
        if status not in WRITTEN:
            status = "generated"
        if definition is None:
            fallback += 1
        new_manifest["documents"].append(
            build_legacy_entry(
                definition, legacy_doc, path, group, status,
                provenance, generated_at, project["tier"], write_order, version,
            )
        )
        adopted += 1
        entry_detail = (
            f"adopted as {status} ({detail})"
            if definition is not None
            else f"adopted as {status} without catalog match ({detail})"
        )
        reports.append({"doc": path, "action": "migrate", "detail": entry_detail})
        if (
            needs_rewrite
            and status in WRITTEN
            and path.endswith(".md")
            and (repo / path).name not in MARKDOWN_EXCEPTIONS
            and not dry_run
        ):
            target = repo / path
            text = target.read_text(encoding="utf-8", errors="replace")
            _write_output(repo, legacy_doc, text, provenance, dry_run)
    if not dry_run:
        manifest_path.write_text(dump_json(new_manifest), encoding="utf-8")
    try:
        manifest_label = str(manifest_path.relative_to(repo))
    except ValueError:
        manifest_label = str(manifest_path)
    reports.insert(
        0,
        {
            "doc": manifest_label,
            "action": "migrate",
            "detail": (
                f"manifest version -> {MANIFEST_CURRENT}; re-registered from {version} "
                f"({adopted} adopted, {kept_planned} planned/in-progress, "
                f"{skipped} skipped, {failed} failed, {fallback} generic)"
            ),
        },
    )
    flow_index_report = migrate_flow_index(repo, dry_run)
    if flow_index_report is not None:
        reports.append(flow_index_report)
    return reports, bool(adopted or kept_planned or failed)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--report", action="store_true")
    args = parser.parse_args()
    if not args.repo.is_dir():
        return fail(f"not a directory: {args.repo}", 2)
    manifest_path = args.manifest or (args.repo / ".docforge" / "manifest.json")
    if args.manifest and not args.manifest.is_absolute():
        candidate = (args.repo / args.manifest).resolve()
        manifest_path = candidate if candidate.exists() else args.manifest.resolve()
    try:
        reports, changed = migrate(args.repo.resolve(), Path(manifest_path).resolve(), args.dry_run)
    except (ValueError, json.JSONDecodeError, OSError) as exc:
        return fail(str(exc), 2)
    migrated = sum(1 for item in reports if item["action"] == "migrate")
    regenerated = sum(1 for item in reports if item["action"] == "regenerate")
    failed = [item for item in reports if item["action"] == "failed"]
    missing = [item for item in reports if item["action"] == "missing"]
    if args.report or args.dry_run:
        print(json.dumps({"changed": changed, "results": reports}, indent=2, ensure_ascii=False))
    else:
        print(
            f"Migrated {migrated} metadata targets; regenerated {regenerated}; "
            f"failed {len(failed)}."
        )
        for item in missing:
            print(f"MISSING  {item['doc']}  ({item['detail']})")
        for item in reports:
            if item["action"] == "regenerate":
                print(f"REGENERATED  {item['doc']}  ({item['detail']})")
            elif item["action"] == "failed":
                print(f"FAILED  {item['doc']}  ({item['detail']})")
    return 1 if missing or failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
