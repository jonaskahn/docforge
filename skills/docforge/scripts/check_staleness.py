#!/usr/bin/env python3
"""Check Docforge 2.0 section provenance using only JSON and the standard library."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

FRONTMATTER = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)
WRITTEN = {"generated", "needs_review", "complete"}
BLOB = re.compile(r"^[0-9a-f]{40}$")


def fail(message: str, code: int = 2) -> int:
    print(f"error: {message}", file=sys.stderr)
    return code


def load_manifest(path: Path) -> dict:
    if not path.is_file():
        raise ValueError(f"manifest not found: {path}")
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if manifest.get("version") != "3.0":
        raise ValueError(
            f"manifest must use version 3.0: {path}; "
            "manifest v2 is unsupported in Docforge 2.0"
        )
    return manifest


def parse_frontmatter(path: Path) -> tuple[str, dict | None]:
    if not path.is_file() or path.suffix.lower() != ".md":
        return "missing", None
    match = FRONTMATTER.match(path.read_text(encoding="utf-8", errors="replace"))
    if not match:
        return "missing", None
    try:
        data = json.loads(match.group(1))
    except json.JSONDecodeError:
        return "unparseable", None
    provenance = data.get("docforge_provenance") if isinstance(data, dict) else None
    if not isinstance(provenance, dict):
        return "missing", None
    if "schema" not in provenance:
        return "legacy", provenance
    return "ok", provenance


def git_blob(path: Path) -> str | None:
    if not path.is_file():
        return None
    content = path.read_bytes()
    header = f"blob {len(content)}\0".encode("ascii")
    return hashlib.sha1(header + content).hexdigest()


def sync_provenance(manifest: dict, repo: Path) -> tuple[int, list[dict], set[str]]:
    updated = 0
    results: list[dict] = []
    failed: set[str] = set()
    for doc in manifest["documents"]:
        if doc.get("provenance_mode") == "manifest":
            continue
        state, provenance = parse_frontmatter(repo / doc["path"])
        if state != "ok":
            failed.add(doc["path"])
            if state == "unparseable":
                results.append({"doc": doc["path"], "status": "UNPARSEABLE", "detail": "invalid frontmatter JSON"})
            else:
                detail = "legacy provenance" if state == "legacy" else "missing provenance"
                results.append({"doc": doc["path"], "status": "UNTRACKED", "detail": detail})
            continue
        doc["provenance"] = provenance
        updated += 1
    return updated, results, failed


def check(
    manifest: dict,
    repo: Path,
    section_filter: str | None,
    skipped: set[str] | None = None,
) -> tuple[list[dict], bool]:
    results: list[dict] = []
    clean = True
    for doc in manifest["documents"]:
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
        stale = []
        for section in matching:
            for source in section.get("sources", []):
                source_path = source.get("path", "")
                recorded = source.get("git_blob")
                if not isinstance(recorded, str) or not BLOB.fullmatch(recorded):
                    stale.append({
                        "doc": doc["path"], "status": "PARTIAL",
                        "section": section.get("id"), "file_status": "NO_BLOB", "file": source_path,
                    })
                    continue
                current = git_blob(repo / source_path)
                if current is None:
                    stale.append({
                        "doc": doc["path"], "status": "PARTIAL",
                        "section": section.get("id"), "file_status": "MISSING", "file": source_path,
                    })
                elif current != recorded:
                    stale.append({
                        "doc": doc["path"], "status": "PARTIAL",
                        "section": section.get("id"), "file_status": "STALE", "file": source_path,
                    })
        if stale:
            results.extend(stale)
            clean = False
        else:
            results.append({"doc": doc["path"], "status": "FRESH"})
    return results, clean


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--section")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--sync-provenance", action="store_true")
    args = parser.parse_args()
    try:
        manifest = load_manifest(args.manifest)
    except (ValueError, json.JSONDecodeError) as exc:
        return fail(str(exc))
    repo = Path(manifest.get("project", {}).get("root") or args.manifest.parent.parent).resolve()
    synchronized = None
    sync_results: list[dict] = []
    sync_failed: set[str] = set()
    if args.sync_provenance:
        synchronized, sync_results, sync_failed = sync_provenance(manifest, repo)
        args.manifest.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    results, clean = check(manifest, repo, args.section, sync_failed)
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
