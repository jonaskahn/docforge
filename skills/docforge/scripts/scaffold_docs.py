#!/usr/bin/env python3
"""Preview, materialize, or audit the exact tree in a Docforge 2.0 manifest."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path, PurePosixPath

SKILL_ROOT = Path(__file__).resolve().parent.parent
TEMPLATES = SKILL_ROOT / "assets" / "templates"
PLACEHOLDER = re.compile(r"\{\{[^}]+\}\}|TODO\([^)]*\)")
TOKEN = re.compile(r"<[A-Z][A-Z0-9_]{2,}>")
LINK = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
FORGE = re.compile(
    r"\b(github|gitlab|bitbucket|gitea|forgejo|sourcehut|azure devops|"
    r"github actions|gitlab ci|codeowners)\b",
    re.IGNORECASE,
)
FRONTMATTER = re.compile(r"\A---\n([^\n]*)\n---\n")
MARKDOWN_EXCEPTIONS = {"AGENTS.md", "CLAUDE.md", "CLAUDE.local.md"}


def fail(message: str, code: int = 1) -> int:
    print(f"error: {message}", file=sys.stderr)
    return code


def resolve_manifest(value: Path, repo: Path) -> Path:
    if value.is_absolute():
        return value
    direct = value.resolve()
    repo_relative = (repo / value).resolve()
    return direct if direct.exists() else repo_relative


def load_manifest(path: Path) -> dict:
    if not path.is_file():
        raise ValueError(f"manifest not found: {path}")
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if manifest.get("version") != "2.0" or not isinstance(manifest.get("documents"), list):
        raise ValueError(f"manifest must use version 2.0: {path}")
    return manifest


def active_documents(manifest: dict) -> list[dict]:
    return [doc for doc in manifest["documents"] if doc.get("status") != "skipped"]


def preview(manifest: dict) -> int:
    docs = active_documents(manifest)
    for doc in docs:
        print(f"{doc['write_order']:03d}  {doc['id']:<28}  {doc['path']}")
    print(f"\n{len(docs)} manifest documents.")
    return 0


def title_for(doc: dict) -> str:
    return Path(doc["path"]).stem.replace("-", " ").replace("_", " ").title()


def index_body(doc: dict, manifest: dict) -> str:
    directory = PurePosixPath(doc["path"]).parent
    children = []
    for candidate in active_documents(manifest):
        if candidate["id"] == doc["id"]:
            continue
        candidate_path = PurePosixPath(candidate["path"])
        try:
            relative = candidate_path.relative_to(directory)
        except ValueError:
            continue
        if len(relative.parts) == 1 or (len(relative.parts) == 2 and relative.name == "README.md"):
            children.append(candidate)
    lines = [
        "---",
        '{"docforge_provenance":{"sections":[]}}',
        "---",
        f"# {title_for(doc)}",
        "",
        "_Last reviewed: {{YYYY-MM-DD}}_",
        "",
        "| Document | Purpose |",
        "|---|---|",
    ]
    for child in sorted(children, key=lambda item: (item["write_order"], item["path"])):
        relative = PurePosixPath(child["path"]).relative_to(directory).as_posix()
        lines.append(f"| [{title_for(child)}]({relative}) | {{{{Describe {child['id']} from repository evidence.}}}} |")
    if not children:
        lines.append("| {{document}} | {{purpose}} |")
    return "\n".join(lines) + "\n"


def scaffold_body(doc: dict, manifest: dict) -> str:
    if doc["type"] in {
        "folder-index", "docs-index", "portfolio-index", "decision-index",
        "portfolio-decisions-index", "ba-index", "po-index",
    }:
        return index_body(doc, manifest)
    template = TEMPLATES / doc["scaffold_template"]
    if not template.is_file():
        raise ValueError(f"template not found for {doc['id']}: {doc['scaffold_template']}")
    return template.read_text(encoding="utf-8")


def deep_merge(existing, defaults):
    if isinstance(existing, dict) and isinstance(defaults, dict):
        result = dict(existing)
        for key, value in defaults.items():
            result[key] = deep_merge(result[key], value) if key in result else value
        return result
    if isinstance(existing, list) and isinstance(defaults, list):
        return existing + [item for item in defaults if item not in existing]
    return existing


def ensure_local_ignore(repo: Path) -> None:
    ignore = repo / ".gitignore"
    text = ignore.read_text(encoding="utf-8") if ignore.exists() else ""
    lines = text.splitlines()
    if "CLAUDE.local.md" not in lines:
        suffix = "" if not text or text.endswith("\n") else "\n"
        ignore.write_text(text + suffix + "CLAUDE.local.md\n", encoding="utf-8")


def write_document(repo: Path, doc: dict, manifest: dict) -> str:
    target = repo / doc["path"]
    body = scaffold_body(doc, manifest)
    target.parent.mkdir(parents=True, exist_ok=True)
    if doc["type"] == "machine-config" and target.exists():
        existing = json.loads(target.read_text(encoding="utf-8"))
        defaults = json.loads(body)
        target.write_text(json.dumps(deep_merge(existing, defaults), indent=2) + "\n", encoding="utf-8")
        action = "merge"
    elif target.exists():
        action = "exists"
    else:
        target.write_text(body, encoding="utf-8")
        action = "create"
    if doc["path"] == "CLAUDE.local.md":
        ensure_local_ignore(repo)
    print(f"{action}  {doc['path']}")
    return action


def required_indexes(doc: dict, manifest: dict) -> list[dict]:
    doc_path = PurePosixPath(doc["path"])
    ancestors = []
    parent = doc_path.parent
    while str(parent) not in ("", "."):
        ancestors.append((parent / "README.md").as_posix())
        parent = parent.parent
    by_path = {item["path"]: item for item in active_documents(manifest)}
    indexes = [by_path[path] for path in reversed(ancestors) if path in by_path and path != doc["path"]]
    return indexes


def materialize(repo: Path, manifest: dict, doc_id: str) -> int:
    matches = [doc for doc in active_documents(manifest) if doc["id"] == doc_id]
    if not matches:
        return fail(f"document id not found or skipped: {doc_id}", 2)
    doc = matches[0]
    try:
        for index in required_indexes(doc, manifest):
            if not (repo / index["path"]).exists():
                write_document(repo, index, manifest)
        write_document(repo, doc, manifest)
    except (ValueError, json.JSONDecodeError) as exc:
        return fail(str(exc), 2)
    return 0


def parse_frontmatter(text: str) -> dict | None:
    match = FRONTMATTER.match(text)
    if not match:
        return None
    try:
        value = json.loads(match.group(1))
    except json.JSONDecodeError:
        return None
    return value if isinstance(value, dict) else None


def audit(repo: Path, manifest: dict) -> int:
    findings: dict[str, list[str]] = {
        "missing": [],
        "unfilled scaffold": [],
        "invalid provenance": [],
        "broken links": [],
        "invalid json": [],
        "folder-only promotion": [],
        "forge leakage": [],
        "unexpected": [],
    }
    tokens: list[str] = []
    docs = active_documents(manifest)
    expected = {doc["path"] for doc in docs}
    for root_name in ("docs", "docs-portfolio"):
        root = repo / root_name
        if root.is_dir():
            for existing in root.rglob("*.md"):
                rel = existing.relative_to(repo).as_posix()
                if "_archive" not in existing.parts and rel not in expected:
                    findings["unexpected"].append(rel)
    for doc in docs:
        target = repo / doc["path"]
        if not target.is_file():
            findings["missing"].append(doc["path"])
            continue
        text = target.read_text(encoding="utf-8", errors="replace")
        if doc["type"] == "machine-config":
            try:
                json.loads(text)
            except json.JSONDecodeError:
                findings["invalid json"].append(doc["path"])
            continue
        placeholders = PLACEHOLDER.findall(text)
        if placeholders:
            findings["unfilled scaffold"].append(f"{doc['path']} ({len(placeholders)})")
        found_tokens = sorted(set(TOKEN.findall(text)))
        if found_tokens:
            tokens.append(f"{doc['path']}: {', '.join(found_tokens)}")
        forge_hits = sorted({match.group(0).lower() for match in FORGE.finditer(text)})
        if forge_hits:
            findings["forge leakage"].append(f"{doc['path']}: {', '.join(forge_hits)}")
        if doc["provenance_mode"] == "sections" and doc["path"] not in MARKDOWN_EXCEPTIONS:
            frontmatter = parse_frontmatter(text)
            if not frontmatter or "docforge_provenance" not in frontmatter:
                findings["invalid provenance"].append(doc["path"])
        for link in LINK.findall(text):
            clean = link.split("#", 1)[0]
            if not clean or clean.startswith(("http://", "https://", "mailto:")):
                continue
            if PLACEHOLDER.search(clean) or TOKEN.search(clean):
                continue
            if not (target.parent / clean).resolve().exists():
                findings["broken links"].append(f"{doc['path']} -> {link}")
    for prefix in ("docs/flows/", "docs/architecture/concepts/"):
        folders = {
            str(PurePosixPath(path).parent)
            for path in expected
            if path.startswith(prefix) and len(PurePosixPath(path).parts) > len(PurePosixPath(prefix).parts)
        }
        for folder in sorted(folders):
            if folder == prefix.rstrip("/"):
                continue
            if f"{folder}/README.md" in expected:
                children = [
                    path for path in expected
                    if str(PurePosixPath(path).parent) == folder and not path.endswith("/README.md")
                ]
                if not children:
                    findings["folder-only promotion"].append(folder)
    total = sum(len(items) for items in findings.values())
    for label, items in findings.items():
        items.sort()
        if items:
            print(f"{label.upper()} ({len(items)})")
            for item in items:
                print(f"  {item}")
            print()
    if tokens:
        print(f"EXTERNAL TOKENS ({len(tokens)})")
        for item in tokens:
            print(f"  {item}")
        print()
    print(f"{len(docs)} manifest documents checked, {total} defects.")
    return 1 if total else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--dry-run", action="store_true")
    modes.add_argument("--document")
    modes.add_argument("--audit", action="store_true")
    args = parser.parse_args()
    if not args.repo.is_dir():
        return fail(f"not a directory: {args.repo}", 2)
    try:
        manifest = load_manifest(resolve_manifest(args.manifest, args.repo))
    except (ValueError, json.JSONDecodeError) as exc:
        return fail(str(exc), 2)
    if args.dry_run:
        return preview(manifest)
    if args.document:
        return materialize(args.repo, manifest, args.document)
    return audit(args.repo, manifest)


if __name__ == "__main__":
    raise SystemExit(main())
