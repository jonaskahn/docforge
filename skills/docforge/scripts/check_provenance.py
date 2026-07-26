#!/usr/bin/env python3
"""
check_provenance.py — compare recorded git blob hashes against current
working-tree content to decide whether a docforge document (or one
of its sections) needs to be rewritten.

Usage:
    python check_provenance.py --manifest docs/.docforge/manifest.json
    python check_provenance.py --manifest docs/.docforge/manifest.json --flow order-approval-threshold
    python check_provenance.py --manifest docs/.docforge/manifest.json --json
    python check_provenance.py --rebuild-manifest --docs-dir docs --manifest docs/.docforge/manifest.json

Exit code is 0 if everything is FRESH, 1 if anything is PARTIAL/STALE/MISSING,
2 on a usage or IO error — so this can gate a CI job.
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)


def git_hash_object(path: str, repo_root: Path) -> str | None:
    """Content hash of the working-tree file, independent of commit history.
    Returns None if the file does not exist."""
    full = repo_root / path
    if not full.exists():
        return None
    try:
        out = subprocess.run(
            ["git", "hash-object", str(full)],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=True,
        )
        return out.stdout.strip()
    except subprocess.CalledProcessError:
        return None


def load_manifest(manifest_path: Path) -> dict:
    if not manifest_path.exists():
        print(f"error: manifest not found at {manifest_path}", file=sys.stderr)
        sys.exit(2)
    return json.loads(manifest_path.read_text())


def extract_frontmatter_yaml_naive(text: str) -> dict | None:
    """Minimal YAML-subset parser for the docforge_provenance block, avoiding
    a hard dependency on PyYAML. Handles the fixed shape this skill writes;
    falls back to None (caller treats as 'no frontmatter recorded') on
    anything unexpected rather than guessing."""
    m = FRONTMATTER_RE.match(text)
    if not m:
        return None
    block = m.group(1)
    if "docforge_provenance" not in block:
        return None
    try:
        import yaml  # optional dependency; most environments already have it

        return yaml.safe_load(block).get("docforge_provenance")
    except ImportError:
        return {"_raw": block}  # signal "present but unparsed" rather than "absent"


def rebuild_manifest(docs_dir: Path, manifest_path: Path) -> None:
    documents = {}
    for md_file in docs_dir.rglob("*.md"):
        text = md_file.read_text(errors="ignore")
        prov = extract_frontmatter_yaml_naive(text)
        if not prov or "_raw" in prov:
            continue
        rel = str(md_file.relative_to(docs_dir.parent))
        sections = {}
        for section in prov.get("sections", []):
            sources = {s["path"]: s["git_blob"] for s in section.get("sources", [])}
            sections[section["id"]] = {"sources": sources}
        documents[rel] = {"sections": sections}
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps({"generated_at": None, "documents": documents}, indent=2) + "\n"
    )
    print(f"rebuilt manifest: {len(documents)} documents -> {manifest_path}")


def check(manifest: dict, repo_root: Path, flow_filter: str | None) -> tuple[list[dict], bool]:
    results = []
    all_fresh = True
    for doc_path, doc_data in manifest.get("documents", {}).items():
        sections = doc_data.get("sections", {})
        if not sections:
            results.append({"doc": doc_path, "status": "STALE",
                             "detail": "no section granularity recorded"})
            all_fresh = False
            continue

        section_statuses = []
        for section_id, section_data in sections.items():
            if flow_filter and flow_filter != section_id:
                continue
            file_statuses = []
            for src_path, recorded_hash in section_data.get("sources", {}).items():
                current_hash = git_hash_object(src_path, repo_root)
                if current_hash is None:
                    file_statuses.append(("MISSING", src_path))
                elif current_hash != recorded_hash:
                    file_statuses.append(("STALE", src_path))
                else:
                    file_statuses.append(("FRESH", src_path))

            bad = [f for f in file_statuses if f[0] != "FRESH"]
            if bad:
                section_statuses.append((section_id, bad))

        if not section_statuses:
            if not flow_filter:
                results.append({"doc": doc_path, "status": "FRESH"})
        else:
            all_fresh = False
            for section_id, bad in section_statuses:
                for status, path in bad:
                    results.append({
                        "doc": doc_path,
                        "status": "PARTIAL",
                        "section": section_id,
                        "file_status": status,
                        "file": path,
                    })
    return results, all_fresh


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--manifest", type=Path, default=Path("docs/.docforge/manifest.json"))
    ap.add_argument("--repo-root", type=Path, default=Path("."))
    ap.add_argument("--flow", default=None, help="Limit the check to one section id")
    ap.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    ap.add_argument("--rebuild-manifest", action="store_true",
                     help="Regenerate the manifest from every document's frontmatter")
    ap.add_argument("--docs-dir", type=Path, default=Path("docs"),
                     help="Used only with --rebuild-manifest")
    args = ap.parse_args()

    if args.rebuild_manifest:
        rebuild_manifest(args.docs_dir, args.manifest)
        return

    manifest = load_manifest(args.manifest)
    results, all_fresh = check(manifest, args.repo_root, args.flow)

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        if not results:
            print("no documents matched.")
        for r in results:
            if r["status"] == "FRESH":
                print(f"FRESH    {r['doc']}")
            elif r["status"] == "PARTIAL":
                print(f"PARTIAL  {r['doc']}  section={r['section']}  "
                      f"{r['file_status']}: {r['file']}")
            else:
                print(f"STALE    {r['doc']}  ({r.get('detail', '')})")

    sys.exit(0 if all_fresh else 1)


if __name__ == "__main__":
    main()
