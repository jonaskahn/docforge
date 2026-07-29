#!/usr/bin/env python3
"""Migrate Docforge manifest 3.0 / provenance 1.0 metadata to 3.1 / 2.0 YAML.

When a document cannot be converted (missing, unparseable, or legacy
frontmatter), regenerate a fresh provenance-2.0 YAML scaffold from the
manifest entry and keep the Markdown body.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from provenance_frontmatter import (
    LEGACY_SCHEMA,
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


def provenance_from_manifest(doc: dict, manifest: dict) -> dict:
    project = manifest.get("project", {}) if isinstance(manifest.get("project"), dict) else {}
    embedded = doc.get("provenance") if isinstance(doc.get("provenance"), dict) else {}
    tier = embedded.get("tier") or project.get("tier") or "<TIER>"
    target_depth = embedded.get("target_depth") or doc.get("target_depth") or "<TARGET_DEPTH>"
    graph = embedded.get("graph") if isinstance(embedded.get("graph"), dict) else {}
    generated = scaffold_provenance(
        doc.get("id") or embedded.get("doc_id") or "<DOC_ID>",
        doc.get("path") or embedded.get("path") or "<DOCUMENT_PATH>",
        tier=str(tier),
        target_depth=str(target_depth),
        provider=str(graph.get("provider") or "<GRAPH_PROVIDER>"),
        flow=str(graph.get("flow") or "<FLOW_CAPABILITY>"),
        generated_at=str(embedded.get("generated_at") or "<GENERATED_AT>"),
    )
    if isinstance(embedded.get("sections"), list) and embedded["sections"]:
        # Preserve section evidence only when the object already looks schema-shaped.
        if embedded.get("schema") in {SCHEMA_VERSION, LEGACY_SCHEMA} or "tool_version" in embedded:
            try:
                return migrate_v1_to_v2(embedded)
            except Exception:
                pass
    return generated


def regenerate_document(repo: Path, doc: dict, manifest: dict, dry_run: bool, reason: str) -> dict:
    path = repo / doc["path"]
    text = path.read_text(encoding="utf-8", errors="replace")
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


def migrate_document_file(repo: Path, doc: dict, manifest: dict, dry_run: bool) -> dict:
    path = repo / doc["path"]
    result = {"doc": doc["path"], "action": "skip", "detail": ""}
    if doc.get("provenance_mode") == "manifest" or path.name in MARKDOWN_EXCEPTIONS:
        result["detail"] = "manifest-only provenance"
        return result
    if not path.is_file() or path.suffix.lower() != ".md":
        result["action"] = "missing"
        result["detail"] = "file absent"
        return result
    text = path.read_text(encoding="utf-8", errors="replace")
    state, provenance, _end = parse_frontmatter(text)
    if state in {"missing", "unparseable", "legacy"}:
        reasons = {
            "missing": "missing provenance",
            "unparseable": "unparseable provenance",
            "legacy": "legacy provenance without schema",
        }
        return regenerate_document(repo, doc, manifest, dry_run, reasons[state])
    if state == "ok" and not needs_provenance_migration(provenance):
        result["detail"] = "already schema 2.0"
        return result
    if state not in {"ok", "obsolete"} or not isinstance(provenance, dict):
        return regenerate_document(
            repo, doc, manifest, dry_run, f"unsupported state {state}"
        )
    if provenance.get("schema") not in {SCHEMA_VERSION, LEGACY_SCHEMA} and "tool_version" not in provenance:
        return regenerate_document(
            repo, doc, manifest, dry_run,
            f"unsupported schema {provenance.get('schema')}",
        )
    _raw, body, _ = split_frontmatter(text)
    try:
        migrated = migrate_v1_to_v2(provenance, body)
    except Exception as exc:
        return regenerate_document(repo, doc, manifest, dry_run, f"conversion failed: {exc}")
    result["action"] = "migrate"
    result["detail"] = f"schema {provenance.get('schema')} -> {SCHEMA_VERSION}"
    if not dry_run:
        path.write_text(rewrite_frontmatter(text, migrated), encoding="utf-8")
    doc["provenance"] = migrated
    return result


def migrate_manifest_object(manifest: dict) -> bool:
    changed = False
    if manifest.get("version") == MANIFEST_LEGACY:
        manifest["version"] = MANIFEST_CURRENT
        changed = True
    for doc in manifest.get("documents", []):
        provenance = doc.get("provenance")
        if needs_provenance_migration(provenance):
            try:
                doc["provenance"] = migrate_v1_to_v2(provenance)
            except Exception:
                doc["provenance"] = provenance_from_manifest(doc, manifest)
            changed = True
        elif not isinstance(provenance, dict) or not provenance:
            doc["provenance"] = provenance_from_manifest(doc, manifest)
            changed = True
    return changed


def migrate(repo: Path, manifest_path: Path, dry_run: bool) -> tuple[list[dict], bool]:
    manifest = load_manifest(manifest_path)
    reports: list[dict] = []
    object_changed = migrate_manifest_object(manifest)
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
        reports.append(migrate_document_file(repo, doc, manifest, dry_run))
    if not dry_run:
        migrate_manifest_object(manifest)
        manifest_path.write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    changed = any(item["action"] in {"migrate", "regenerate"} for item in reports)
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
    missing = [item for item in reports if item["action"] == "missing"]
    if args.report or args.dry_run:
        print(json.dumps({"changed": changed, "results": reports}, indent=2, ensure_ascii=False))
    else:
        print(f"Migrated {migrated} metadata targets; regenerated {regenerated}.")
        for item in missing:
            print(f"MISSING  {item['doc']}  ({item['detail']})")
        for item in reports:
            if item["action"] == "regenerate":
                print(f"REGENERATED  {item['doc']}  ({item['detail']})")
    return 1 if missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
