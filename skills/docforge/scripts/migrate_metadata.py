#!/usr/bin/env python3
"""Migrate Docforge manifest 3.0 / provenance 1.0 metadata to 3.1 / 2.0 YAML.

Converts schema 1.0 and schema-less legacy frontmatter (including pre-schema
`doc` / `graph_snapshot` shapes) while preserving section evidence. When a
document cannot be converted to complete provenance 2.0 (missing or
unparseable frontmatter, conversion failure, or incomplete result for a
written document), write a best-effort scaffold, mark the document
`in_progress` for agent regeneration, and report `failed`.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from provenance_frontmatter import (
    FLOW_VALUES,
    LEGACY_SCHEMA,
    SCAFFOLD_TOKEN,
    SCHEMA_VERSION,
    emit_yaml,
    migrate_v1_to_v2,
    parse_frontmatter,
    rewrite_frontmatter,
    scaffold_provenance,
    split_frontmatter,
)

MANIFEST_CURRENT = "3.1"
MANIFEST_LEGACY = "3.0"
MARKDOWN_EXCEPTIONS = {"AGENTS.md", "CLAUDE.md", "CLAUDE.local.md"}
WRITTEN = {"generated", "needs_review", "complete"}
SCALAR_FIELDS = ("doc_id", "path", "generated_at", "tier", "target_depth")


def fail(message: str, code: int = 1) -> int:
    print(f"error: {message}", file=sys.stderr)
    return code


def load_manifest(path: Path) -> dict:
    if not path.is_file():
        raise ValueError(f"manifest not found: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    version = data.get("version")
    if version not in {MANIFEST_CURRENT, MANIFEST_LEGACY}:
        raise ValueError(
            f"manifest must use version {MANIFEST_CURRENT} or {MANIFEST_LEGACY}: {path}; "
            "older manifests are unsupported"
        )
    return data


def needs_provenance_migration(provenance: dict | None) -> bool:
    if not isinstance(provenance, dict):
        return False
    if "schema" not in provenance:
        return False
    if provenance.get("schema") == SCHEMA_VERSION and "generator" in provenance and "tool_version" not in provenance:
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
    body = body_for_rewrite(text)
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
    if not dry_run:
        path.write_text(emit_yaml(generated) + body.lstrip("\n"), encoding="utf-8")
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
    path = repo / doc["path"]
    body = body_for_rewrite(text)
    generated = provenance_from_manifest(doc, manifest)
    result = {
        "doc": doc["path"],
        "action": "regenerate",
        "detail": f"{reason}; wrote provenance {SCHEMA_VERSION} scaffold from manifest",
    }
    if not dry_run:
        path.write_text(emit_yaml(generated) + body.lstrip("\n"), encoding="utf-8")
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
    path = repo / doc["path"]
    result = {"doc": doc["path"], "action": "migrate", "detail": detail}
    if not dry_run:
        path.write_text(rewrite_frontmatter(text, migrated), encoding="utf-8")
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
        result["detail"] = "already schema 2.0"
        return result
    if state not in {"ok", "obsolete"} or not isinstance(provenance, dict):
        if must_complete:
            return fail_document(
                repo, doc, manifest, dry_run, f"unsupported state {state}", text=text,
            )
        return regenerate_planned(
            repo, doc, manifest, dry_run, f"unsupported state {state}", text,
        )
    if provenance.get("schema") not in {SCHEMA_VERSION, LEGACY_SCHEMA} and "tool_version" not in provenance:
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


def migrate_manifest_object(manifest: dict, *, demote_incomplete: bool = False) -> bool:
    changed = False
    if manifest.get("version") == MANIFEST_LEGACY:
        manifest["version"] = MANIFEST_CURRENT
        changed = True
    for doc in manifest.get("documents", []):
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
    manifest = load_manifest(manifest_path)
    reports: list[dict] = []
    # Snapshot written status before any demotion so file conversion can still
    # require complete provenance 2.0 for previously published documents.
    require_complete = {
        doc["id"]: doc.get("status") in WRITTEN
        for doc in manifest.get("documents", [])
        if isinstance(doc.get("id"), str)
    }
    object_changed = migrate_manifest_object(manifest, demote_incomplete=False)
    try:
        manifest_label = str(manifest_path.relative_to(repo))
    except ValueError:
        manifest_label = str(manifest_path)
    if object_changed:
        reports.append({
            "doc": manifest_label,
            "action": "migrate",
            "detail": f"manifest version -> {MANIFEST_CURRENT}; provenance objects normalized",
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
        migrate_manifest_object(manifest, demote_incomplete=True)
        manifest_path.write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    changed = any(
        item["action"] in {"migrate", "regenerate", "failed"} for item in reports
    )
    return reports, changed


def ensure_migrated(repo: Path, manifest_path: Path) -> dict:
    """Migrate in place and return the loaded current manifest."""
    migrate(repo, manifest_path, dry_run=False)
    return load_manifest(manifest_path)


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
