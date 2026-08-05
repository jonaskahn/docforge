#!/usr/bin/env python3
"""Docforge dashboard runtime.

Backs the dashboard capability of the `docforge` skill (the optional
`/docforge-dashboard` skill is only a thin entrypoint into this cartridge).
Builds and serves a local Fumadocs application under `<repo>/.docforge/dashboard/`
from the Docforge manifest and the repository's `docs/` Markdown. The dashboard
directory is self-contained: its own package.json, lockfile, and node_modules;
it never touches the repository's package files.

Subcommands: scan, start, status, stop. Python and JS peers are equivalent.

`start` is idempotent: it scans for documentation problems, reconciles
metadata, compares working-tree signatures, rebuilds generated output only
when the render or shell signature changed (or `--force`), installs
dependencies only when missing, starts (or reuses) the localhost dev server,
and opens the browser. The dev server runs detached; `stop` shuts it down.
`scan` is the read-only diagnostic pass: missing metadata, incomplete or
missing documents, stale provenance sources, broken internal links, and
untracked `docs/` files.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import posixpath
import re
import shutil
import socket
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from runtime.common.python._util import (
    dump_json,
    ensure_docforge_gitignore,
    fail,
    load_manifest,
    read_json,
)
from runtime.common.python.provenance_frontmatter import (
    SCHEMA_VERSION,
    emit_document_frontmatter,
    parse_yaml_mapping,
    split_frontmatter,
)

TOOL_VERSION = "2.14.0"
TEMPLATE_VERSION = "1"
STATE_SCHEMA = 1
STATE_FILE = ".docforge-dashboard.json"
BASE_URL = "/docs"
DOC_PREFIX = "docs/"
WRITTEN = {"generated", "needs_review", "complete"}
FRONTMATTER_HEAD_BYTES = 64 * 1024
ASSET_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".avif", ".ico", ".bmp"}
ASSET_MAX_BYTES = 10 * 1024 * 1024
LINK_RE = re.compile(r"(!?\[[^\]]*\])(\(([^)\s]+)(?:\s+[\"'][^\"']*[\"'])?\))")
HEADING_RE = re.compile(r"^\s{0,3}(#{1,6})\s+(.+?)\s*#*\s*$")
CUSTOM_ANCHOR_RE = re.compile(r"\[#([^\]]+)\]$")
SCHEMES = ("http://", "https://", "mailto:", "tel:", "//")
ENTITY = {"<": "&lt;", ">": "&gt;", "{": "&#123;", "}": "&#125;"}


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def title_for(doc: dict) -> str:
    return doc.get("title") or doc["id"].replace("-", " ").replace("_", " ").title()


def git_remote_url(repo: Path) -> str | None:
    result = subprocess.run(
        ["git", "-C", str(repo), "config", "--get", "remote.origin.url"],
        capture_output=True, text=True, timeout=10,
    )
    value = result.stdout.strip() if result.returncode == 0 else ""
    if not value:
        return None
    value = value.removesuffix(".git")
    if value.startswith("git@"):
        value = value.replace(":", "/", 1).replace("git@", "https://", 1)
    if value.startswith(("http://", "https://")):
        return value
    return None


def _root_doc_has_provenance(repo: Path, path: str) -> bool:
    meta = file_metadata(repo, path)
    return meta is not None and meta["provenance_schema"] == SCHEMA_VERSION


def read_frontmatter_head(target: Path) -> tuple[str, int] | None:
    """Read only a document's frontmatter block from the file head (bounded
    read; the body is never read). Returns (raw, body_start) or None when the
    file has no frontmatter. Falls back to a full read only when the
    frontmatter exceeds the head bound."""
    try:
        with open(target, "rb") as handle:
            head = handle.read(FRONTMATTER_HEAD_BYTES)
    except OSError:
        return None
    if not head.startswith(b"---\n"):
        return None
    end = head.find(b"\n---\n", 4)
    if end < 0:
        text = target.read_text(encoding="utf-8", errors="replace")
        raw, body, _end = split_frontmatter(text)
        if raw is None:
            return None
        return raw, len(text) - len(body)
    return head[4:end].decode("utf-8", errors="replace"), end + len("\n---\n")


def file_metadata(repo: Path, rel: str) -> dict | None:
    """Public metadata of a written document read from its frontmatter head
    only: id, title, description, and provenance schema. None when the file
    carries no parseable docforge frontmatter."""
    result = read_frontmatter_head(repo / rel)
    if result is None:
        return None
    raw, _body_start = result
    try:
        data = parse_yaml_mapping(raw)
    except Exception:  # noqa: BLE001 - treated as not docforge-managed
        return None
    provenance = data.get("docforge_provenance")
    return {
        "id": data.get("id"),
        "title": data.get("title"),
        "description": data.get("description"),
        "provenance_schema": provenance.get("schema") if isinstance(provenance, dict) else None,
    }


def _manifest_provenance(doc: dict) -> bool:
    """Root documents with `provenance_mode: manifest` (for example
    `AGENTS.md`) carry no YAML frontmatter; their provenance lives in the
    manifest instead."""
    if doc.get("provenance_mode") != "manifest":
        return False
    provenance = doc.get("provenance")
    return isinstance(provenance, dict) and provenance.get("schema") == SCHEMA_VERSION


def included_documents(repo: Path, manifest: dict) -> list[dict]:
    out = []
    for doc in manifest.get("documents", []):
        if doc.get("status") not in WRITTEN:
            continue
        path = doc.get("path", "")
        if path == "CLAUDE.local.md":
            # gitignored, machine-local preferences: never a shared page
            continue
        if not (path.endswith(".md") or path.endswith(".mdx")):
            continue
        if not (path.startswith(DOC_PREFIX) or "/" not in path):
            continue
        if not (repo / path).is_file():
            continue
        if "/" not in path and not (_root_doc_has_provenance(repo, path) or _manifest_provenance(doc)):
            continue
        out.append(doc)
    return sorted(out, key=lambda d: (d["path"], d["id"]))


def route_for_doc(doc: dict) -> tuple[str, str]:
    path = doc["path"]
    if path.startswith(DOC_PREFIX):
        rel = path[len(DOC_PREFIX):]
        if rel == "README.md":
            return "index.mdx", BASE_URL
        if rel.endswith("/README.md"):
            directory = rel[:-len("/README.md")]
            return f"{directory}/index.mdx", f"{BASE_URL}/{directory}"
        stem = rel[:-3] if rel.endswith(".md") else rel[:-4]
        return f"{stem}.mdx", f"{BASE_URL}/{stem}"
    stem = path[:-3] if path.endswith(".md") else path[:-4]
    slug = stem.lower()
    return f"root/{slug}.mdx", f"{BASE_URL}/root/{slug}"


def build_ledger(docs: list[dict]) -> dict:
    ledger = {"pages": [], "by_path": {}, "by_url": {}}
    for doc in docs:
        output, url = route_for_doc(doc)
        page = {
            "id": doc["id"],
            "doc_id": doc["id"],
            "doc": doc,
            "title": title_for(doc),
            "source_path": doc["path"],
            "output_path": output,
            "url": url,
            "write_order": doc.get("write_order", 0),
            "nav_order": doc.get("nav_order"),
        }
        ledger["pages"].append(page)
        ledger["by_path"][doc["path"]] = page
        ledger["by_url"][url] = page
    return ledger


def tree_files(repo: Path) -> list[str]:
    root = repo / "docs"
    if not root.is_dir():
        return []
    return sorted(
        str(path.relative_to(repo)).replace("\\", "/")
        for path in root.rglob("*")
        if path.is_file()
    )


def _sorted_template_files(template_dir: Path) -> list[Path]:
    return sorted(
        (p for p in template_dir.rglob("*") if p.is_file()),
        key=lambda p: str(p.relative_to(template_dir)),
    )


def _manifest_projection(manifest: dict) -> list[dict]:
    """The manifest fields that affect rendered output: status, path, id,
    title, description, write_order, and nav_order. Everything else (evidence,
    selection, audit records, ...) does not change the site and must not
    trigger a rebuild."""
    docs = []
    for doc in sorted(manifest.get("documents", []), key=lambda d: d.get("path", "")):
        entry = {
            "id": doc.get("id", ""),
            "title": title_for(doc),
            "description": doc.get("description", ""),
            "path": doc.get("path", ""),
            "status": doc.get("status", ""),
            "write_order": doc.get("write_order", 0),
        }
        if doc.get("nav_order") is not None:
            entry["nav_order"] = doc["nav_order"]
        docs.append(entry)
    return docs


def render_signature(repo: Path, manifest: dict) -> str:
    """Working-tree signature of everything that renders: `docs/` file bytes
    (including assets), included root-document bytes, and the manifest
    projection. No git HEAD, no flow index, no repository package files —
    those do not affect the generated site."""
    records: list[str] = []
    projection = _manifest_projection(manifest)
    for doc in projection:
        records.append("doc\x00" + json.dumps(doc, sort_keys=True, separators=(",", ":")))
    for rel in tree_files(repo):
        records.append(f"file\x00{rel}\x00{sha256_bytes((repo / rel).read_bytes())}")
    for doc in projection:
        rel = doc["path"]
        if not rel or "/" in rel or not rel.endswith((".md", ".mdx")):
            continue
        target = repo / rel
        if target.is_file():
            records.append(f"root\x00{rel}\x00{sha256_bytes(target.read_bytes())}")
    settings = {
        "base_url": BASE_URL,
        "generator": TOOL_VERSION,
        "include": "docs/**, root/*.md",
    }
    records.append("settings\x00" + json.dumps(settings, sort_keys=True, separators=(",", ":")))
    return sha256_bytes("\n".join(records).encode("utf-8"))


def shell_signature(template_dir: Path, repo: Path, manifest: dict) -> str:
    """Signature of the Fumadocs application shell: template file bytes, the
    per-project `lib/shared.ts` inputs (app name, repository URL), and the
    template version."""
    records: list[str] = []
    for path in _sorted_template_files(template_dir):
        rel = str(path.relative_to(template_dir)).replace("\\", "/")
        records.append(f"template\x00{rel}\x00{sha256_bytes(path.read_bytes())}")
    project = {
        "name": manifest.get("project", {}).get("name") or repo.resolve().name,
        "git_url": git_remote_url(repo) or "",
    }
    records.append("project\x00" + json.dumps(project, sort_keys=True, separators=(",", ":")))
    records.append(f"template_version\x00{TEMPLATE_VERSION}")
    return sha256_bytes("\n".join(records).encode("utf-8"))


def state_path(dashboard: Path) -> Path:
    return dashboard / STATE_FILE


def load_state(dashboard: Path) -> dict:
    path = state_path(dashboard)
    if path.is_file():
        try:
            value = read_json(path)
            if isinstance(value, dict):
                return value
        except ValueError:
            pass
    return {}


def save_state(dashboard: Path, state: dict) -> None:
    dashboard.mkdir(parents=True, exist_ok=True)
    state_path(dashboard).write_text(dump_json(state), encoding="utf-8")


def public_frontmatter(
    doc_id: str,
    title: str,
    provenance: dict,
    description: str | None = None,
) -> str:
    return emit_document_frontmatter(doc_id, title, provenance, description or None)


def reconcile_metadata(repo: Path, manifest: dict, dry_run: bool = False) -> dict:
    report = {"reconciled": [], "unchanged": [], "skipped": [], "errors": []}
    for doc in manifest.get("documents", []):
        if doc.get("status") == "skipped" or doc.get("provenance_mode") == "manifest":
            continue
        path = doc.get("path", "")
        if not path.startswith(DOC_PREFIX) or not path.endswith(".md"):
            continue
        target = repo / path
        if not target.is_file():
            continue
        head = read_frontmatter_head(target)
        if head is None:
            report["skipped"].append({"doc": doc["id"], "detail": "no frontmatter"})
            continue
        raw, _body_start = head
        try:
            data = parse_yaml_mapping(raw)
        except Exception as exc:  # noqa: BLE001 - report and continue
            report["errors"].append({"doc": doc["id"], "detail": f"unparseable frontmatter: {exc}"})
            continue
        provenance = data.get("docforge_provenance")
        if not isinstance(provenance, dict) or provenance.get("schema") != SCHEMA_VERSION:
            report["skipped"].append({"doc": doc["id"], "detail": "provenance is not schema 2.0"})
            continue
        want_id = doc["id"]
        want_title = title_for(doc)
        want_description = doc.get("description") or ""
        problems = []
        if data.get("id") != want_id:
            problems.append("id")
        if data.get("title") != want_title:
            problems.append("title")
        if (data.get("description") or "") != want_description:
            problems.append("description")
        if provenance.get("doc_id") != want_id:
            problems.append("provenance.doc_id")
        if provenance.get("path") != path:
            problems.append("provenance.path")
        if not problems:
            report["unchanged"].append({"doc": doc["id"]})
            continue
        entry = {"doc": doc["id"], "path": path, "fixed": problems}
        if not dry_run:
            if "provenance.doc_id" in problems:
                provenance["doc_id"] = want_id
            if "provenance.path" in problems:
                provenance["path"] = path
            text = target.read_text(encoding="utf-8", errors="replace")
            _raw, body, _end = split_frontmatter(text)
            target.write_text(
                public_frontmatter(want_id, want_title, provenance, want_description) + body,
                encoding="utf-8",
            )
        report["reconciled"].append(entry)
    report["counts"] = {
        "reconciled": len(report["reconciled"]),
        "unchanged": len(report["unchanged"]),
        "errors": len(report["errors"]),
    }
    return report


def escape_mdx_text(line: str) -> str:
    out: list[str] = []
    in_code = False
    for char in line:
        if char == "`":
            in_code = not in_code
            out.append(char)
        elif in_code:
            out.append(char)
        else:
            out.append(ENTITY.get(char, char))
    return "".join(out)


def strip_html_comments(body: str) -> str:
    """Remove HTML comments outside fenced and inline code.

    Docforge keeps management markers such as ``<!-- docforge-children:start
    -->`` in source Markdown so scaffolds can be re-expanded; the dashboard
    must never render them. Comments (including multiline ones) are dropped
    while the content between markers is kept, and comment text inside fenced
    or inline code is preserved verbatim.
    """
    out: list[str] = []
    in_fence = False
    in_comment = False
    for line in body.splitlines(keepends=True):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            out.append(line)
            continue
        if in_fence:
            out.append(line)
            continue
        line_out: list[str] = []
        in_code = False
        i = 0
        length = len(line)
        while i < length:
            char = line[i]
            if in_comment:
                end = line.find("-->", i)
                if end < 0:
                    i = length
                    continue
                in_comment = False
                i = end + 3
                continue
            if char == "`":
                in_code = not in_code
                line_out.append(char)
                i += 1
                continue
            if not in_code and line.startswith("<!--", i):
                end = line.find("-->", i + 4)
                if end < 0:
                    in_comment = True
                    i = length
                    continue
                i = end + 3
                continue
            line_out.append(char)
            i += 1
        out.append("".join(line_out))
    return "".join(out)


def resolve_link(target: str, source_path: str, ledger: dict, assets_needed: set[str]) -> str | None:
    """Resolve a link target written in `source_path` through the route ledger.

    Returns the rewritten URL; `target` unchanged when it is a bare fragment;
    or None when the target is left untouched (external schemes, or an
    internal target with no ledger page or asset)."""
    index = target.find("#")
    fragment = target[index:] if index >= 0 else ""
    clean = target[:index] if index >= 0 else target
    if not clean:
        return target
    if clean.startswith(SCHEMES) or clean.startswith("#"):
        return None
    base = posixpath.dirname(source_path)
    repo_rel = clean.lstrip("/") if clean.startswith("/") else posixpath.normpath(posixpath.join(base, clean))
    repo_rel = repo_rel.rstrip("/")
    page = ledger["by_path"].get(repo_rel)
    if page is None and not repo_rel.endswith(".md"):
        page = ledger["by_path"].get(f"{repo_rel}/README.md")
    if page is not None:
        return page["url"] + fragment
    if repo_rel in ledger["assets"]:
        assets_needed.add(repo_rel)
        return f"/docs-assets/{repo_rel}" + fragment
    return None


def convert_body(body: str, source_path: str, ledger: dict, assets_needed: set[str]) -> tuple[str, list[str]]:
    unresolved: list[str] = []
    body = strip_html_comments(body)

    def replace(match: re.Match) -> str:
        inner = match.group(3)
        rewritten = resolve_link(inner, source_path, ledger, assets_needed)
        if rewritten is None or rewritten == inner:
            return match.group(0)
        return f"{match.group(1)}({rewritten})"

    in_fence = False
    lines: list[str] = []
    for line in body.splitlines(keepends=True):
        stripped = line.lstrip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            lines.append(line)
            continue
        converted_line = escape_mdx_text(line) if not in_fence else line
        lines.append(LINK_RE.sub(replace, converted_line) if not in_fence else converted_line)
    return "".join(lines), unresolved


def first_h1_title(body: str) -> str | None:
    """Extract the first H1 heading as the document's meaningful title.

    Strips Fumadocs heading markers (`[!toc]`, `[toc]`, `[#custom-id]`),
    link syntax, and inline formatting. Returns None when there is no H1 so
    callers can fall back to the manifest title.
    """
    for line in body.splitlines():
        match = re.match(r"^\s{0,3}#\s+(.+?)\s*#*\s*$", line)
        if not match:
            continue
        text = match.group(1)
        text = re.sub(r"(\s*\[(?:[!#]|toc)[^\]]*\])+\s*$", "", text)
        text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)
        text = re.sub(r"[*_`]", "", text)
        text = re.sub(r"\s+", " ", text).strip()
        if text:
            return text
    return None


def heading_anchors(text: str) -> list[str]:
    anchors: list[str] = []
    for line in text.splitlines():
        match = HEADING_RE.match(line)
        if not match:
            continue
        content = match.group(2).strip()
        custom = CUSTOM_ANCHOR_RE.search(content)
        if custom:
            anchors.append(custom.group(1))
            continue
        slug = re.sub(r"[^\w\s-]", "", content).lower()
        slug = re.sub(r"\s+", "-", slug).strip("-")
        anchors.append(slug)
    return anchors


def collect_asset_map(repo: Path) -> set[str]:
    return {
        rel for rel in tree_files(repo)
        if rel.endswith(tuple(ASSET_EXTS))
    }


def blob_sha1(content: bytes) -> str:
    return hashlib.sha1(b"blob %d\0" % len(content) + content).hexdigest()


def scan(repo: Path, manifest: dict) -> dict:
    """Read-only diagnostics over the manifest and `docs/` tree.

    Reports metadata problems (missing / unparseable / non-schema-2.0
    frontmatter), incomplete or missing documents, provenance source drift,
    broken internal Markdown links, and untracked `docs/` files. Any finding
    means the documentation should be revised before the dashboard is
    trusted; `counts` groups findings by kind."""
    problems: list[dict] = []
    report = reconcile_metadata(repo, manifest, dry_run=True)
    for entry in report["errors"]:
        problems.append({"kind": "metadata", "doc": entry["doc"], "detail": entry["detail"]})
    for entry in report["skipped"]:
        problems.append({"kind": "metadata", "doc": entry["doc"], "detail": entry["detail"]})
    for doc in manifest.get("documents", []):
        path = doc.get("path", "")
        if not (path.endswith(".md") or path.endswith(".mdx")):
            continue
        if doc.get("status") not in WRITTEN:
            problems.append({"kind": "incomplete", "doc": doc.get("id", ""), "detail": f"status {doc.get('status')}"})
            continue
        if not (repo / path).is_file():
            problems.append({"kind": "missing_file", "doc": doc.get("id", ""), "detail": path})
    for doc in manifest.get("documents", []):
        provenance = doc.get("provenance")
        if not isinstance(provenance, dict) or provenance.get("schema") != SCHEMA_VERSION:
            continue
        for section in provenance.get("sections", []):
            for source in section.get("sources", []):
                source_path = source.get("path")
                want = source.get("git_blob")
                if not source_path:
                    continue
                target = repo / source_path
                if not target.is_file():
                    problems.append({"kind": "drift", "doc": doc.get("id", ""), "detail": f"{source_path} missing"})
                    continue
                if want and blob_sha1(target.read_bytes()) != want:
                    problems.append({"kind": "drift", "doc": doc.get("id", ""), "detail": f"{source_path} changed since provenance"})
    docs = included_documents(repo, manifest)
    ledger = build_ledger(docs)
    ledger["assets"] = collect_asset_map(repo)
    tracked = {doc.get("path") for doc in manifest.get("documents", []) if doc.get("path")}
    for rel in tree_files(repo):
        if rel.endswith((".md", ".mdx")) and rel not in tracked:
            problems.append({"kind": "untracked", "doc": "", "detail": rel})
    for doc in docs:
        text = (repo / doc["path"]).read_text(encoding="utf-8", errors="replace")
        raw, body, _end = split_frontmatter(text)
        if raw is None:
            body = text
        for match in LINK_RE.finditer(body):
            inner = match.group(3)
            if resolve_link(inner, doc["path"], ledger, set()) is not None:
                continue
            clean = inner.split("#", 1)[0]
            if not clean or clean.startswith(SCHEMES) or clean.startswith("#"):
                continue
            repo_rel = clean.lstrip("/") if clean.startswith("/") else posixpath.normpath(
                posixpath.join(posixpath.dirname(doc["path"]), clean)
            )
            repo_rel = repo_rel.rstrip("/")
            if re.search(r"\.mdx?(?:#|$)", repo_rel) and (
                repo_rel.startswith(DOC_PREFIX) or "/" not in repo_rel
            ):
                problems.append({"kind": "broken_link", "doc": doc["id"], "detail": f"{doc['path']}: {inner}"})
    kinds = ("metadata", "incomplete", "missing_file", "drift", "untracked", "broken_link")
    counts = {kind: sum(1 for p in problems if p["kind"] == kind) for kind in kinds}
    return {"problems": problems, "counts": counts}


def plan(repo: Path, manifest: dict) -> dict:
    docs = included_documents(repo, manifest)
    ledger = build_ledger(docs)
    problems: list[str] = []
    folded: dict[str, str] = {}
    for page in ledger["pages"]:
        key = page["url"].lower()
        if key in folded:
            problems.append(f"duplicate url: {page['url']} (docs {folded[key]} and {page['source_path']})")
        else:
            folded[key] = page["source_path"]
    by_dir: dict[str, list[dict]] = {}
    for page in ledger["pages"]:
        by_dir.setdefault(posixpath.dirname(page["output_path"]), []).append(page)
    missing_index = any(page["url"] == BASE_URL for page in ledger["pages"])
    if not missing_index:
        problems.append("no docs index: docs/README.md is not a written document")
    return {
        "base_url": BASE_URL,
        "pages": ledger["pages"],
        "folder_count": len(by_dir),
        "problems": problems,
    }


def meta_title(folder: str, ledger: dict, manifest: dict) -> str:
    for page in ledger["pages"]:
        if page["output_path"] == (f"{folder}/index.mdx" if folder else "index.mdx"):
            return page["title"]
    if folder == "":
        for doc in manifest.get("documents", []):
            if doc.get("id") == "docs_index":
                return title_for(doc)
    if folder == "root":
        return "Project"
    name = posixpath.basename(folder)
    return name.replace("-", " ").replace("_", " ").title()


def page_order(page: dict) -> int:
    """Navigation order of a page: the curated `nav_order` when present
    (reader-first sidebar), falling back to the generation `write_order`."""
    nav = page.get("nav_order")
    return nav if isinstance(nav, int) else page["write_order"]


def meta_plans(ledger: dict, manifest: dict) -> dict[str, dict]:
    folders: dict[str, dict] = {}
    for page in ledger["pages"]:
        folder = posixpath.dirname(page["output_path"])
        folders.setdefault(folder, {"index": None, "files": [], "orders": {}})
        if posixpath.basename(page["output_path"]) == "index.mdx":
            folders[folder]["index"] = page
        else:
            folders[folder]["files"].append(page)
        folders[folder]["orders"][page["doc_id"]] = page_order(page)
    for folder in folders:
        folders[folder]["files"].sort(key=lambda p: (page_order(p), p["source_path"]))

    def folder_order(folder: str) -> tuple[int, str]:
        """Meaningful order: a folder is ordered by its index document's
        nav_order (falling back to the manifest write_order), else by the
        smallest order among its pages, with the folder name as the
        deterministic tie-break. The `root` folder (repository-root files
        such as README.md and CHANGELOG.md) always sorts last."""
        if folder == "root":
            return (10**9, folder)
        info = folders.get(folder)
        if info is None:
            return (10**9, folder)
        if info["index"] is not None:
            return (page_order(info["index"]), folder)
        return (min((page_order(p) for p in info["files"]), default=10**9), folder)

    plans: dict[str, dict] = {}
    for folder, info in folders.items():
        names = {
            posixpath.relpath(other, folder).split("/", 1)[0]
            for other in folders
            if other != folder and (not folder or other.startswith(folder + "/"))
        }
        entries: list[tuple[tuple[int, str], str]] = []
        for name in names:
            order, _ = folder_order(posixpath.join(folder, name))
            entries.append(((order, name), name))
        for page in info["files"]:
            stem = posixpath.splitext(posixpath.basename(page["output_path"]))[0]
            entries.append(((page_order(page), stem), stem))
        entries.sort(key=lambda item: item[0])
        pages = []
        if info["index"] is not None:
            pages.append("index")
        pages.extend(name for _, name in entries)
        plans[folder] = {
            "path": f"{folder}/meta.json" if folder else "meta.json",
            "title": meta_title(folder, ledger, manifest),
            "pages": pages,
        }
    return plans


def convert_documents(repo: Path, manifest: dict, ledger: dict, stage_docs: Path) -> dict:
    assets_needed: set[str] = set()
    anchors: dict[str, list[str]] = {}
    converted = []
    for doc in ledger["pages"]:
        source = repo / doc["source_path"]
        text = source.read_text(encoding="utf-8", errors="replace")
        raw, body, _end = split_frontmatter(text)
        if raw is None:
            manifest_doc = doc.get("doc") or {}
            provenance = manifest_doc.get("provenance")
            if (
                manifest_doc.get("provenance_mode") != "manifest"
                or not isinstance(provenance, dict)
                or provenance.get("schema") != SCHEMA_VERSION
            ):
                raise ValueError(f"document has no frontmatter: {doc['source_path']}")
        else:
            try:
                data = parse_yaml_mapping(raw)
            except Exception as exc:  # noqa: BLE001
                raise ValueError(f"unparseable frontmatter: {doc['source_path']}: {exc}") from exc
            provenance = data.get("docforge_provenance")
            if not isinstance(provenance, dict) or provenance.get("schema") != SCHEMA_VERSION:
                raise ValueError(f"provenance is not schema 2.0: {doc['source_path']}")
        mdx_body, unresolved = convert_body(body, doc["source_path"], ledger, assets_needed)
        h1_title = first_h1_title(body)
        if h1_title:
            doc["title"] = h1_title
        page = {"id": doc["doc_id"], "title": doc["title"]}
        manifest_doc = doc.get("doc") or {}
        content = public_frontmatter(
            page["id"],
            page["title"],
            provenance,
            manifest_doc.get("description"),
        ) + mdx_body
        target = stage_docs / doc["output_path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        anchors[doc["url"]] = heading_anchors(mdx_body)
        converted.append({"doc": doc["doc_id"], "url": doc["url"], "output": doc["output_path"], "unresolved": unresolved})
    return {"converted": converted, "assets_needed": sorted(assets_needed), "anchors": anchors}


def copy_assets(repo: Path, target_assets_dir: Path, assets: list[str]) -> list[str]:
    copied = []
    for rel in assets:
        source = repo / rel
        if not source.is_file() or not rel.endswith(tuple(ASSET_EXTS)):
            continue
        if source.stat().st_size > ASSET_MAX_BYTES:
            continue
        target = target_assets_dir / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        copied.append(rel)
    return copied


def swap_stage(dashboard: Path, stage_docs: Path, stage_assets: Path) -> None:
    content_target = dashboard / "content" / "docs"
    if content_target.exists():
        shutil.rmtree(content_target)
    os.rename(stage_docs, content_target)
    assets_target = dashboard / "public" / "docs-assets"
    if assets_target.exists():
        shutil.rmtree(assets_target)
    if stage_assets.exists():
        os.rename(stage_assets, assets_target)


def validate_build(repo: Path, manifest: dict, content_dir: Path, assets_dir: Path) -> dict:
    docs = included_documents(repo, manifest)
    ledger = build_ledger(docs)
    errors: list[str] = []
    warnings: list[str] = []
    folded: dict[str, str] = {}
    for page in ledger["pages"]:
        key = page["url"].lower()
        if key in folded:
            errors.append(f"duplicate url: {page['url']} ({folded[key]}, {page['source_path']})")
        else:
            folded[key] = page["source_path"]
        output = content_dir / page["output_path"]
        if not output.is_file():
            errors.append(f"missing output: {page['output_path']} ({page['url']})")
    if not (content_dir / "index.mdx").is_file():
        errors.append("missing docs index: content/docs/index.mdx")
    url_to_page = {page["url"]: page for page in ledger["pages"]}
    anchors: dict[str, set[str]] = {}
    for page in ledger["pages"]:
        output = content_dir / page["output_path"]
        if output.is_file():
            anchors[page["url"]] = set(heading_anchors(output.read_text(encoding="utf-8", errors="replace")))
    link_re = re.compile(r"\]\(([^)]+)\)")
    for page in ledger["pages"]:
        output = content_dir / page["output_path"]
        if not output.is_file():
            continue
        text = output.read_text(encoding="utf-8", errors="replace")
        for match in link_re.finditer(text):
            target = match.group(1).strip()
            if target.startswith(("#", "http://", "https://", "mailto:", "tel:", "//")):
                continue
            if target.startswith(f"{BASE_URL}/") or target == BASE_URL or target.startswith(f"{BASE_URL}#"):
                hash_index = target.find("#")
                url = target[:hash_index] if hash_index >= 0 else target
                fragment = target[hash_index:] if hash_index >= 0 else ""
                if url not in url_to_page:
                    errors.append(f"broken link in {page['output_path']}: {target}")
                    continue
                if fragment and fragment.lstrip("#") not in anchors.get(url, set()):
                    errors.append(f"broken anchor in {page['output_path']}: {target}")
            elif target.startswith("/docs-assets/"):
                asset = target[len("/docs-assets/"):].split("#", 1)[0]
                if not (assets_dir / asset).is_file():
                    errors.append(f"missing asset in {page['output_path']}: {target}")
            else:
                target_path = target.split("#", 1)[0]
                normalized = posixpath.normpath(
                    posixpath.join(DOC_PREFIX, posixpath.dirname(page["output_path"]), target_path)
                )
                if re.search(r"\.mdx?(?:#|$)", normalized) and (
                    normalized.startswith(DOC_PREFIX) or "/" not in normalized
                ):
                    errors.append(f"unresolved internal link in {page['output_path']}: {target}")
                else:
                    warnings.append(f"unresolved target in {page['output_path']}: {target}")
    meta_paths = sorted((content_dir / "meta.json").parent.rglob("meta.json")) if (content_dir / "meta.json").exists() else []
    for meta_file in meta_paths:
        folder = str(meta_file.parent.relative_to(content_dir)).replace("\\", "/")
        if folder == ".":
            folder = ""
        try:
            data = read_json(meta_file)
        except ValueError:
            errors.append(f"invalid meta.json: {meta_file}")
            continue
        expected_children = set()
        for page in ledger["pages"]:
            parent = posixpath.dirname(page["output_path"])
            if parent == folder:
                expected_children.add(posixpath.splitext(posixpath.basename(page["output_path"]))[0])
        for child in sorted((meta_file.parent).iterdir()):
            if child.is_dir() and (child / "meta.json").is_file():
                expected_children.add(child.name)
        actual = set(data.get("pages", []))
        for missing in sorted(expected_children - actual):
            errors.append(f"meta coverage missing in {meta_file.relative_to(dashboard)}: {missing}")
        for extra in sorted(actual - expected_children):
            errors.append(f"meta coverage extra in {meta_file.relative_to(dashboard)}: {extra}")
    return {
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
        "counts": {
            "pages": len(ledger["pages"]),
            "meta_files": len(meta_paths),
        },
    }


def ensure_dashboard_ignored(dashboard: Path) -> None:
    """Keep `.docforge/.gitignore` authoritative for Docforge's ephemeral dirs
    (shared rules) and additionally declare the dashboard directory itself."""
    ensure_docforge_gitignore(dashboard.parent)
    gitignore = dashboard.parent / ".gitignore"
    lines = gitignore.read_text(encoding="utf-8").splitlines()
    if "dashboard/" not in lines:
        text = gitignore.read_text(encoding="utf-8")
        suffix = "" if not text or text.endswith("\n") else "\n"
        gitignore.write_text(text + suffix + "dashboard/\n", encoding="utf-8")


def scaffold_app(dashboard: Path, template_dir: Path, repo: Path, manifest: dict, force: bool = False) -> bool:
    current = load_state(dashboard)
    sha = shell_signature(template_dir, repo, manifest)
    if not force and current.get("shell_sig") == sha and (dashboard / "lib" / "shared.ts").is_file():
        return False
    for name in ("app", "components", "lib", "next.config.mjs", "tsconfig.json", "postcss.config.mjs", "package.json", ".gitignore", "README.md"):
        source = template_dir / name
        target = dashboard / name
        if source.is_dir():
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(source, target)
        elif source.is_file():
            shutil.copy2(source, target)
    project_name = manifest.get("project", {}).get("name") or repo.resolve().name
    git_url = git_remote_url(repo) or ""
    tpl = (template_dir / "lib" / "shared.ts.tpl").read_text(encoding="utf-8")
    shared = tpl.replace("{{APP_NAME}}", project_name).replace("{{GITHUB_URL}}", git_url)
    (dashboard / "lib" / "shared.ts").write_text(shared, encoding="utf-8")
    ensure_dashboard_ignored(dashboard)
    return True


def node_major() -> int:
    try:
        result = subprocess.run(["node", "--version"], capture_output=True, text=True, timeout=10)
        version = result.stdout.strip().lstrip("v") if result.returncode == 0 else ""
        return int(version.split(".", 1)[0]) if version else 0
    except Exception:  # noqa: BLE001
        return 0


def build_dashboard(dashboard: Path) -> None:
    """Static HTML export: `next build` emits plain .html files under `out/`
    (the app is a static-export Next.js app, `output: 'export'`)."""
    env = dict(os.environ, NEXT_TELEMETRY_DISABLED="1")
    try:
        subprocess.run(
            ["npm", "--prefix", str(dashboard), "run", "build"],
            cwd=str(dashboard),
            env=env,
            check=True,
            timeout=1200,
        )
    except subprocess.CalledProcessError as exc:
        raise ValueError(f"dashboard export failed (exit {exc.returncode}); see the dashboard directory for logs") from exc


def export_signature(render_sig: str, shell_sig: str) -> str:
    return sha256_bytes(f"{render_sig}\n{shell_sig}".encode("utf-8"))


def ensure_dependencies(dashboard: Path, repo: Path) -> None:
    if node_major() < 22:
        raise ValueError("dashboard requires Node.js 22 or newer; install it before running /docforge-dashboard")
    root_guards = {}
    for name in ("package.json", "package-lock.json"):
        root_file = repo / name
        if root_file.is_file():
            root_guards[name] = sha256_bytes(root_file.read_bytes())
    node_modules = dashboard / "node_modules"
    lockfile = dashboard / "package-lock.json"
    if not node_modules.is_dir() or not lockfile.is_file():
        command = ["npm", "--prefix", str(dashboard), "install"]
    else:
        command = ["npm", "--prefix", str(dashboard), "ci"]
    env = dict(os.environ, NEXT_TELEMETRY_DISABLED="1")
    try:
        subprocess.run(command, cwd=str(dashboard), env=env, check=True, timeout=900)
    except subprocess.CalledProcessError as exc:
        raise ValueError(f"npm install failed (exit {exc.returncode}); see the dashboard directory for logs") from exc
    for name, before in root_guards.items():
        after = sha256_bytes((repo / name).read_bytes()) if (repo / name).is_file() else None
        if after != before:
            raise ValueError(f"dashboard touched the repository's {name}; refusing to continue")


def free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except (ProcessLookupError, PermissionError):
        return False
    except OSError:
        return False


def server_up(port: int) -> bool:
    try:
        urllib.request.urlopen(f"http://127.0.0.1:{port}{BASE_URL}", timeout=2)
        return True
    except Exception:  # noqa: BLE001 - any HTTP response or refusal
        return False


def wait_for_server(port: int, log_path: Path, timeout: int = 180) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if server_up(port):
            return
        time.sleep(0.25)
    tail = ""
    if log_path.is_file():
        lines = log_path.read_text(encoding="utf-8", errors="replace").splitlines()
        tail = "\n".join(lines[-40:])
    raise ValueError(f"dashboard server did not start within {timeout}s; last log lines:\n{tail}")


def ensure_server(dashboard: Path, requested_port: int | None) -> dict:
    state = load_state(dashboard)
    log_path = dashboard / "dev.log"
    if state.get("pid") and state.get("dashboard") == str(dashboard.resolve()):
        if isinstance(state.get("pid"), int) and pid_alive(state["pid"]) and isinstance(state.get("port"), int):
            if server_up(state["port"]):
                return {"pid": state["pid"], "port": state["port"], "reused": True, "url": f"http://127.0.0.1:{state['port']}{BASE_URL}"}
    port = requested_port if isinstance(requested_port, int) and requested_port > 0 else free_port()
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log = open(log_path, "a", encoding="utf-8")
    proc = subprocess.Popen(
        ["npm", "--prefix", str(dashboard), "run", "dev", "--", "-H", "127.0.0.1", "-p", str(port)],
        cwd=str(dashboard),
        stdout=log,
        stderr=subprocess.STDOUT,
        env=dict(os.environ, NEXT_TELEMETRY_DISABLED="1"),
        start_new_session=True,
    )
    new_state = dict(state)
    new_state.update({
        "schema": STATE_SCHEMA,
        "dashboard": str(dashboard.resolve()),
        "pid": proc.pid,
        "port": port,
        "url": f"http://127.0.0.1:{port}{BASE_URL}",
        "started_at": now_iso(),
    })
    save_state(dashboard, new_state)
    try:
        wait_for_server(port, log_path)
    except ValueError:
        proc.terminate()
        raise
    return {"pid": proc.pid, "port": port, "reused": False, "url": new_state["url"]}


def process_group_alive(pid: int) -> bool:
    try:
        os.waitpid(pid, os.WNOHANG)
    except (ChildProcessError, OSError):
        pass
    try:
        os.killpg(pid, 0)
        return True
    except PermissionError:
        return True
    except ProcessLookupError:
        return False
    except OSError:
        return pid_alive(pid)


def signal_process_group(pid: int, signum: int) -> bool:
    try:
        os.killpg(pid, signum)
        return True
    except (ProcessLookupError, PermissionError):
        try:
            os.kill(pid, signum)
            return True
        except OSError:
            return False
    except OSError:
        return False


def stop_server(dashboard: Path) -> dict:
    state = load_state(dashboard)
    pid = state.get("pid")
    stopped = isinstance(pid, int) and pid > 0
    forced = False
    if stopped and process_group_alive(pid):
        signal_process_group(pid, 15)  # SIGTERM
        deadline = time.time() + 3
        while process_group_alive(pid) and time.time() < deadline:
            time.sleep(0.05)
        if process_group_alive(pid):
            forced = signal_process_group(pid, 9)  # SIGKILL
    state.pop("pid", None)
    state.pop("port", None)
    state.pop("url", None)
    save_state(dashboard, state)
    return {"stopped": stopped, "forced": forced}


def open_browser(url: str) -> None:
    try:
        opener = "open" if sys.platform == "darwin" else "xdg-open"
        subprocess.run([opener, url], timeout=10, capture_output=True)
    except Exception:  # noqa: BLE001 - browser opening must never fail the run
        pass


def _stage_build(dashboard: Path, repo: Path, manifest: dict, template_dir: Path, force: bool) -> dict:
    """Scaffold (when needed), convert into staging, validate staging, then
    swap into place. A failed conversion or validation leaves the previous
    dashboard untouched."""
    state = load_state(dashboard)
    shell_sig = shell_signature(template_dir, repo, manifest)
    scaffold_app(dashboard, template_dir, repo, manifest, force or state.get("shell_sig") != shell_sig)
    route_plan = plan(repo, manifest)
    if route_plan["problems"]:
        for problem in route_plan["problems"]:
            print(f"problem: {problem}")
        print("route plan has errors; fix the manifest or document tree before starting")
        raise ValueError("route plan has errors")
    content_dir = dashboard / "content"
    staging = content_dir / ".staging"
    stage_docs = staging / "docs"
    stage_assets = staging / "public" / "docs-assets"
    if staging.exists():
        shutil.rmtree(staging)
    stage_docs.mkdir(parents=True, exist_ok=True)
    try:
        ledger = build_ledger(included_documents(repo, manifest))
        ledger["assets"] = collect_asset_map(repo)
        converted = convert_documents(repo, manifest, ledger, stage_docs)
        meta = meta_plans(ledger, manifest)
        for folder, item in meta.items():
            meta_path = stage_docs / item["path"]
            meta_path.parent.mkdir(parents=True, exist_ok=True)
            meta_path.write_text(dump_json({"title": item["title"], "pages": item["pages"]}), encoding="utf-8")
        copied = copy_assets(repo, stage_assets, converted["assets_needed"])
        validation = validate_build(repo, manifest, stage_docs, stage_assets)
        for warning in validation["warnings"]:
            print(f"  warning: {warning}")
        if not validation["ok"]:
            for error in validation["errors"]:
                print(f"  error: {error}")
            raise ValueError("dashboard validation failed; previous dashboard left in place")
        swap_stage(dashboard, stage_docs, stage_assets)
        if staging.exists():
            shutil.rmtree(staging)
        return {"converted": converted["converted"], "copied": copied, "validation": validation}
    except Exception:
        if staging.exists():
            shutil.rmtree(staging)
        print("dashboard was NOT opened: the documentation failed the dashboard build; run /docforge-revise to fix it, then `dashboard start` again")
        raise


def _plan_only(args: argparse.Namespace, manifest: dict, render_sig: str, shell_sig: str) -> int:
    metadata_report = reconcile_metadata(args.repo, manifest, dry_run=True)
    route_plan = plan(args.repo, manifest)
    print(f"metadata (dry-run): {metadata_report['counts']['reconciled']} to reconcile, {metadata_report['counts']['unchanged']} unchanged, {metadata_report['counts']['errors']} errors")
    for page in route_plan["pages"]:
        print(f"  {page['doc_id']:<32} {page['source_path']:<48} -> {page['url']}")
    print(f"{len(route_plan['pages'])} pages in {route_plan['folder_count']} folders; {len(route_plan['problems'])} problems")
    for problem in route_plan["problems"]:
        print(f"  problem: {problem}")
    print(f"render_sig: {render_sig}")
    print(f"shell_sig: {shell_sig}")
    ok = not route_plan["problems"] and metadata_report["counts"]["errors"] == 0
    return 0 if ok else 1


def _prepare(args: argparse.Namespace, dashboard: Path, manifest: dict, template_dir: Path, render_sig: str, shell_sig: str, force: bool) -> tuple[dict, str]:
    """Shared `start`/`export` pipeline: scan, metadata reconcile, signature,
    build-if-changed, install-if-missing. Returns (new_state, render_sig)."""
    metadata_report = reconcile_metadata(args.repo, manifest)
    print(f"metadata: {metadata_report['counts']['reconciled']} reconciled, {metadata_report['counts']['unchanged']} unchanged")
    scan_result = scan(args.repo, manifest)
    if scan_result["problems"]:
        print(f"scan: {len(scan_result['problems'])} problems found:")
        for problem in scan_result["problems"]:
            who = f"{problem['doc']}: " if problem["doc"] else ""
            print(f"  [{problem['kind']}] {who}{problem['detail']}")
        print("you should revise again: run /docforge-revise to fix the documentation before relying on this dashboard")
    else:
        print("scan: 0 problems")
    # Reconcile rewrites frontmatter, so the render signature must be computed
    # after it: the stored signature must describe the exact bytes a rebuild
    # would consume.
    render_sig = render_signature(args.repo, manifest)

    state = load_state(dashboard)
    built = (dashboard / "content" / "docs" / "index.mdx").is_file()
    needs_render = force or state.get("render_sig") != render_sig or state.get("shell_sig") != shell_sig or not built
    new_state = dict(state)
    if needs_render:
        result = _stage_build(dashboard, args.repo, manifest, template_dir, force)
        new_state.update({
            "schema": STATE_SCHEMA,
            "dashboard": str(dashboard.resolve()),
            "render_sig": render_sig,
            "shell_sig": shell_sig,
            "built_at": now_iso(),
        })
        save_state(dashboard, new_state)
        print(f"converted {len(result['converted'])} documents; copied {len(result['copied'])} assets")
    else:
        print("signature unchanged: dashboard is up to date")

    if not (dashboard / "node_modules").is_dir():
        ensure_dependencies(dashboard, args.repo)

    return new_state, render_sig


def cmd_start(args: argparse.Namespace, dashboard: Path, manifest: dict, template_dir: Path) -> int:
    render_sig = render_signature(args.repo, manifest)
    shell_sig = shell_signature(template_dir, args.repo, manifest)
    if args.plan_only:
        return _plan_only(args, manifest, render_sig, shell_sig)
    _prepare(args, dashboard, manifest, template_dir, render_sig, shell_sig, args.force)

    server = ensure_server(dashboard, args.port)
    print(f"dashboard: {server['url']} (reused={server['reused']})")
    if not args.no_open:
        open_browser(server["url"])
    print("dashboard server running in the background; stop it with `dashboard stop`")
    return 0


def cmd_export(args: argparse.Namespace, dashboard: Path, manifest: dict, template_dir: Path) -> int:
    render_sig = render_signature(args.repo, manifest)
    shell_sig = shell_signature(template_dir, args.repo, manifest)
    new_state, render_sig = _prepare(args, dashboard, manifest, template_dir, render_sig, shell_sig, False)

    export_sig = export_signature(render_sig, shell_sig)
    out_dir = dashboard / "out"
    has_output = out_dir.is_dir() and any(out_dir.rglob("*.html"))
    needs_export = new_state.get("export_sig") != export_sig or not has_output
    if needs_export:
        build_dashboard(dashboard)
        new_state.update({
            "schema": STATE_SCHEMA,
            "dashboard": str(dashboard.resolve()),
            "export_sig": export_sig,
            "exported_at": now_iso(),
        })
        save_state(dashboard, new_state)
        print(f"exported: {out_dir}")
    else:
        print(f"export up to date: {out_dir}")
    return 0


def cmd_scan(args: argparse.Namespace, manifest: dict) -> int:
    result = scan(args.repo, manifest)
    if args.json:
        print(dump_json(result))
        return 0 if not result["problems"] else 1
    if not result["problems"]:
        print("scan: 0 problems; the documentation is ready to render")
        return 0
    print(f"scan: {len(result['problems'])} problems found:")
    for problem in result["problems"]:
        who = f"{problem['doc']}: " if problem["doc"] else ""
        print(f"  [{problem['kind']}] {who}{problem['detail']}")
    print("you should revise again: run /docforge-revise to fix the documentation, then `dashboard start` again")
    return 1


def cmd_status(args: argparse.Namespace, dashboard: Path, manifest: dict, template_dir: Path) -> int:
    docs = included_documents(args.repo, manifest)
    state = load_state(dashboard)
    render_sig = render_signature(args.repo, manifest)
    running = False
    if state.get("pid") and isinstance(state.get("port"), int):
        running = pid_alive(state["pid"]) and server_up(state["port"])
    result = {
        "dashboard": str(dashboard),
        "exists": dashboard.is_dir(),
        "render_sig": {
            "current": render_sig,
            "stored": state.get("render_sig"),
            "match": state.get("render_sig") == render_sig,
        },
        "server": {
            "running": running,
            "port": state.get("port") if running else None,
            "url": state.get("url") if running else None,
        },
        "counts": {"included_docs": len(docs)},
        "built_at": state.get("built_at"),
    }
    if args.json:
        print(dump_json(result))
    else:
        print(f"dashboard: {result['dashboard']}")
        print(f"exists: {result['exists']}  render signature match: {result['render_sig']['match']}")
        print(f"server: {'running on ' + str(result['server']['url']) if result['server']['running'] else 'not running'}")
        print(f"included documents: {result['counts']['included_docs']}")
    return 0


def cmd_stop(args: argparse.Namespace, dashboard: Path) -> int:
    result = stop_server(dashboard)
    print(f"stopped: {result['stopped']}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="dashboard", description="Docforge dashboard: build-if-changed, serve, or export")
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--repo", default=".", help="repository root (default: current directory)")
    common.add_argument("--manifest", default=None, help="manifest path (default: <repo>/.docforge/manifest.json)")
    common.add_argument("--dashboard", default=None, help="dashboard directory (default: <repo>/.docforge/dashboard)")
    common.add_argument("--json", action="store_true", help="JSON output (status)")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("scan", parents=[common], help="read-only diagnostics: metadata, missing/incomplete docs, source drift, broken links, untracked docs/ files")
    start = sub.add_parser("start", parents=[common], help="reconcile, rebuild when changed, serve, and open")
    start.add_argument("--force", action="store_true", help="rebuild generated output even when the signature is unchanged")
    start.add_argument("--plan-only", action="store_true", help="reconcile dry-run, signatures, and route plan only; no writes, no server")
    start.add_argument("--no-open", action="store_true", help="do not open the browser after serving")
    start.add_argument("--port", type=int, default=0, help="port (default: auto)")
    sub.add_parser("export", parents=[common], help="reconcile, rebuild when changed, then `next build` the static HTML export into out/")
    sub.add_parser("status", parents=[common], help="dashboard existence, render signature match, server state")
    sub.add_parser("stop", parents=[common], help="stop the dashboard dev server")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    repo = Path(args.repo).resolve()
    manifest_path = Path(args.manifest) if args.manifest else repo / ".docforge" / "manifest.json"
    dashboard = Path(args.dashboard).resolve() if args.dashboard else repo / ".docforge" / "dashboard"
    args.repo = repo
    args.manifest = manifest_path
    args.dashboard = dashboard
    template_dir = Path(__file__).resolve().parent.parent / "template"
    if args.command in {"start", "export", "status", "scan"}:
        try:
            manifest = load_manifest(manifest_path)
        except ValueError as exc:
            return fail(str(exc))
    else:
        manifest = {}
    try:
        if args.command == "scan":
            return cmd_scan(args, manifest)
        if args.command == "start":
            return cmd_start(args, dashboard, manifest, template_dir)
        if args.command == "export":
            return cmd_export(args, dashboard, manifest, template_dir)
        if args.command == "status":
            return cmd_status(args, dashboard, manifest, template_dir)
        if args.command == "stop":
            return cmd_stop(args, dashboard)
    except ValueError as exc:
        return fail(str(exc))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
