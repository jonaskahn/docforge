#!/usr/bin/env python3
"""Check Docforge section provenance using only JSON and the standard library."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from runtime.common.python._util import fail, load_manifest
from .migrate_metadata import ensure_migrated
from runtime.common.python.provenance_frontmatter import (
    BLOB,
    SUPPORTED_SCHEMA_VERSIONS,
    migrate_v1_to_v2,
    rewrite_frontmatter,
)
from runtime.common.python import provenance_store as store
from runtime.common.python.evidence_hash import classify_source, git_blob_for_path

WRITTEN = {"generated", "needs_review", "complete"}


def git_blob(path: Path) -> str | None:
    return git_blob_for_path(path)


def matches_document(doc: dict, document_filter: str | None) -> bool:
    if document_filter is None:
        return True
    return doc.get("id") == document_filter or doc.get("path") == document_filter


def _write_back(repo: Path, doc: dict, storage: str, provenance: dict) -> None:
    if storage == store.STORAGE_JSON:
        entry = store.entry_for(repo, doc["path"])
        entry = dict(entry) if isinstance(entry, dict) else {}
        entry["provenance"] = provenance
        store.write_entry(repo, doc["path"], entry)
    else:
        doc_path = repo / doc["path"]
        text = doc_path.read_text(encoding="utf-8", errors="replace")
        doc_path.write_text(rewrite_frontmatter(text, provenance), encoding="utf-8")


def sync_provenance(
    manifest: dict,
    repo: Path,
    document_filter: str | None = None,
) -> tuple[int, list[dict], set[str]]:
    updated = 0
    results: list[dict] = []
    failed: set[str] = set()
    storage = store.storage_for(manifest)
    for doc in manifest["documents"]:
        if not matches_document(doc, document_filter):
            continue
        if doc.get("provenance_mode") == "manifest":
            continue
        meta = store.read_doc_metadata(repo, doc, storage)
        state = meta["state"]
        if state == "inline":
            if store.move_inline_to_sidecar(repo, doc, storage) != "moved":
                failed.add(doc["path"])
                results.append({"doc": doc["path"], "status": "UNTRACKED", "detail": "inline migration failed"})
                continue
            doc["provenance"] = meta["provenance"]
            updated += 1
            continue
        if state == "legacy":
            failed.add(doc["path"])
            results.append({"doc": doc["path"], "status": "UNTRACKED", "detail": "legacy provenance"})
            continue
        if state == "obsolete":
            migrated = migrate_v1_to_v2(meta["provenance"])
            _write_back(repo, doc, storage, migrated)
            doc["provenance"] = migrated
            updated += 1
            continue
        if state != "ok":
            failed.add(doc["path"])
            if state == "unparseable":
                results.append({"doc": doc["path"], "status": "UNPARSEABLE", "detail": "invalid frontmatter"})
            else:
                results.append({"doc": doc["path"], "status": "UNTRACKED", "detail": "missing provenance"})
            continue
        doc["provenance"] = meta["provenance"]
        updated += 1
    return updated, results, failed


def check(
    manifest: dict,
    repo: Path,
    section_filter: str | None,
    skipped: set[str] | None = None,
    document_filter: str | None = None,
) -> tuple[list[dict], bool]:
    results: list[dict] = []
    clean = True
    for doc in manifest["documents"]:
        if not matches_document(doc, document_filter):
            continue
        if doc.get("status") not in WRITTEN:
            continue
        if skipped and doc["path"] in skipped:
            clean = False
            continue
        provenance = doc.get("provenance")
        if not isinstance(provenance, dict) or not provenance:
            results.append({"doc": doc["path"], "status": "UNTRACKED", "detail": "missing provenance"})
            clean = False
            continue
        if provenance.get("schema") not in SUPPORTED_SCHEMA_VERSIONS or "tool_version" in provenance:
            results.append({"doc": doc["path"], "status": "UNTRACKED", "detail": "obsolete schema"})
            clean = False
            continue
        if "schema" not in provenance:
            results.append({"doc": doc["path"], "status": "UNTRACKED", "detail": "legacy provenance"})
            clean = False
            continue
        sections = provenance.get("sections", [])
        matching = [
            section for section in sections
            if section_filter is None or section.get("id") == section_filter
        ]
        if not sections:
            results.append({"doc": doc["path"], "status": "UNTRACKED", "detail": "missing provenance"})
            clean = False
            continue
        if section_filter is not None and not matching:
            continue
        findings = []
        has_blocking = False
        for section in matching:
            for source in section.get("sources", []):
                source_path = source.get("path", "")
                recorded = source.get("git_blob")
                if not isinstance(recorded, str) or not BLOB.fullmatch(recorded):
                    findings.append({
                        "doc": doc["path"], "status": "PARTIAL",
                        "section": section.get("id"), "file_status": "NO_BLOB", "file": source_path,
                    })
                    has_blocking = True
                    continue
                target = repo / source_path
                current_bytes = target.read_bytes() if target.is_file() else None
                outcome = classify_source(source, current_bytes)
                if outcome == "fresh":
                    continue
                file_status = {"missing": "MISSING", "cosmetic": "COSMETIC", "stale": "STALE"}[outcome]
                findings.append({
                    "doc": doc["path"], "status": "PARTIAL",
                    "section": section.get("id"), "file_status": file_status, "file": source_path,
                })
                if outcome != "cosmetic":
                    has_blocking = True
        if findings:
            results.extend(findings)
            if has_blocking:
                clean = False
        else:
            results.append({"doc": doc["path"], "status": "FRESH"})
    return results, clean


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--document", help="Filter by manifest document id or path")
    parser.add_argument("--section")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--sync-provenance", action="store_true")
    args = parser.parse_args()
    manifest_path = args.manifest.resolve()
    try:
        raw = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return fail(str(exc), 2)
    repo = Path(raw.get("project", {}).get("root") or manifest_path.parent.parent).resolve()
    try:
        if args.sync_provenance:
            manifest = ensure_migrated(repo, manifest_path)
        else:
            manifest = load_manifest(manifest_path)
    except ValueError as exc:
        return fail(str(exc), 2)
    synchronized = None
    sync_results: list[dict] = []
    sync_failed: set[str] = set()
    if args.sync_provenance:
        synchronized, sync_results, sync_failed = sync_provenance(
            manifest, repo, args.document,
        )
        manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    results, clean = check(manifest, repo, args.section, sync_failed, args.document)
    if sync_results:
        results = sync_results + results
        clean = False
    if args.json:
        payload = {"synchronized": synchronized, "results": results} if synchronized is not None else results
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        if synchronized is not None:
            print(f"Synchronized provenance for {synchronized} documents.")
        if not results:
            print("no documents matched.")
        for result in results:
            if result["status"] == "FRESH":
                print(f"FRESH      {result['doc']}")
            elif result["status"] == "UNTRACKED":
                print(f"UNTRACKED  {result['doc']}  ({result['detail']})")
            elif result["status"] == "UNPARSEABLE":
                print(f"UNPARSEABLE  {result['doc']}  ({result['detail']})")
            else:
                print(
                    f"PARTIAL    {result['doc']}  section={result['section']}  "
                    f"{result['file_status']}: {result['file']}"
                )
    return 0 if clean else 1


if __name__ == "__main__":
    raise SystemExit(main())
