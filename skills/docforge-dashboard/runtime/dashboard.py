#!/usr/bin/env python3
"""Docforge dashboard runtime.

Backs the `/docforge-dashboard` skill. Builds and serves a local Fumadocs
application under `<repo>/.docforge/dashboard/` from the Docforge manifest
and the repository's `docs/` Markdown. The dashboard directory is
self-contained: its own package.json, lockfile, and node_modules; it never
touches the repository's package files.

Subcommands: metadata, fingerprint, plan, build, validate, serve, stop,
status. Python and JS peers are equivalent.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import posixpath
import re
import signal
import shutil
import socket
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from runtime.common._util import (
    dump_json,
    ensure_docforge_gitignore,
    fail,
    load_manifest,
    read_json,
)
from runtime.common.provenance_frontmatter import (
    SCHEMA_VERSION,
    emit_document_frontmatter,
    parse_yaml_mapping,
    split_frontmatter,
)

TOOL_VERSION = "2.8.0"
TEMPLATE_VERSION = "1"
STATE_SCHEMA = 1
STATE_FILE = ".docforge-dashboard.json"
BASE_URL = "/docs"
DOC_PREFIX = "docs/"
WRITTEN = {"generated", "needs_review", "complete"}
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


def git_head(repo: Path) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD"],
        capture_output=True, text=True, timeout=10,
    )
    return result.stdout.strip() if result.returncode == 0 else ""


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


def included_documents(repo: Path, manifest: dict) -> list[dict]:
    out = []
    for doc in manifest.get("documents", []):
        if doc.get("status") not in WRITTEN:
            continue
        path = doc.get("path", "")
        if not path.startswith(DOC_PREFIX) or not (path.endswith(".md") or path.endswith(".mdx")):
            continue
        if not (repo / path).is_file():
            continue
        out.append(doc)
    return sorted(out, key=lambda d: (d["path"], d["id"]))


def route_for_doc(doc: dict) -> tuple[str, str]:
    path = doc["path"]
    rel = path[len(DOC_PREFIX):]
    if rel == "README.md":
        return "index.mdx", BASE_URL
    if rel.endswith("/README.md"):
        directory = rel[:-len("/README.md")]
        return f"{directory}/index.mdx", f"{BASE_URL}/{directory}"
    stem = rel[:-3] if rel.endswith(".md") else rel[:-4]
    return f"{stem}.mdx", f"{BASE_URL}/{stem}"


def build_ledger(docs: list[dict]) -> dict:
    ledger = {"pages": [], "by_path": {}, "by_url": {}}
    for doc in docs:
        output, url = route_for_doc(doc)
        page = {
            "id": doc["id"],
            "doc_id": doc["id"],
            "title": title_for(doc),
            "source_path": doc["path"],
            "output_path": output,
            "url": url,
            "write_order": doc.get("write_order", 0),
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


def template_sha(template_dir: Path) -> str:
    records = []
    for path in _sorted_template_files(template_dir):
        rel = str(path.relative_to(template_dir)).replace("\\", "/")
        records.append(f"{rel}\x00{sha256_bytes(path.read_bytes())}")
    return sha256_bytes("\n".join(records).encode("utf-8"))


def fingerprint(repo: Path, manifest_path: Path, manifest: dict, template_dir: Path) -> str:
    records: list[str] = []
    records.append(f"head\x00{git_head(repo)}")
    records.append(f"manifest\x00{sha256_bytes(manifest_path.read_bytes())}")
    flow = repo / ".docforge" / "flow-index.json"
    if flow.is_file():
        records.append(f"flow-index\x00{sha256_bytes(flow.read_bytes())}")
    for rel in tree_files(repo):
        records.append(f"docs-file\x00{rel}\x00{sha256_bytes((repo / rel).read_bytes())}")
    for path in _sorted_template_files(template_dir):
        rel = str(path.relative_to(template_dir)).replace("\\", "/")
        records.append(f"template\x00{rel}\x00{sha256_bytes(path.read_bytes())}")
    for name in ("package.json", "package-lock.json"):
        root_file = repo / name
        if root_file.is_file():
            records.append(f"root-{name}\x00{sha256_bytes(root_file.read_bytes())}")
    settings = {
        "base_url": BASE_URL,
        "template_version": TEMPLATE_VERSION,
        "generator": TOOL_VERSION,
        "include": "docs/**",
    }
    records.append(f"settings\x00{json.dumps(settings, sort_keys=True, separators=(',', ':'))}")
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


def public_frontmatter(doc: dict, provenance: dict) -> str:
    return emit_document_frontmatter(doc["id"], title_for(doc), provenance)


def reconcile_metadata(repo: Path, manifest: dict, dry_run: bool = False) -> dict:
    report = {"reconciled": [], "unchanged": [], "skipped": [], "errors": []}
    for doc in manifest.get("documents", []):
        if doc.get("status") == "skipped":
            continue
        path = doc.get("path", "")
        if not path.startswith(DOC_PREFIX) or not path.endswith(".md"):
            continue
        target = repo / path
        if not target.is_file():
            continue
        text = target.read_text(encoding="utf-8", errors="replace")
        raw, body, _end = split_frontmatter(text)
        if raw is None:
            report["skipped"].append({"doc": doc["id"], "detail": "no frontmatter"})
            continue
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
        problems = []
        if data.get("id") != want_id:
            problems.append("id")
        if data.get("title") != want_title:
            problems.append("title")
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
            target.write_text(public_frontmatter(doc, provenance) + body, encoding="utf-8")
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


def convert_body(body: str, source_path: str, ledger: dict, assets_needed: set[str]) -> tuple[str, list[str]]:
    unresolved: list[str] = []
    in_fence = False
    lines: list[str] = []
    for line in body.splitlines(keepends=True):
        stripped = line.lstrip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            lines.append(line)
            continue
        lines.append(escape_mdx_text(line) if not in_fence else line)
    converted = "".join(lines)
    base = posixpath.dirname(source_path)

    def resolve(target: str) -> str | None:
        index = target.find("#")
        fragment = target[index:] if index >= 0 else ""
        clean = target[:index] if index >= 0 else target
        if not clean:
            return target
        if clean.startswith(SCHEMES) or clean.startswith("#"):
            return None
        repo_rel = clean.lstrip("/") if clean.startswith("/") else posixpath.normpath(posixpath.join(base, clean))
        repo_rel = repo_rel.rstrip("/")
        page = ledger["by_path"].get(repo_rel)
        if page is None and repo_rel.endswith("/README.md") is False:
            pass
        if page is None and not repo_rel.endswith(".md"):
            page = ledger["by_path"].get(f"{repo_rel}/README.md")
        if page is not None:
            return page["url"] + fragment
        if repo_rel in ledger["assets"]:
            assets_needed.add(repo_rel)
            return f"/docs-assets/{repo_rel}" + fragment
        return None

    def replace(match: re.Match) -> str:
        inner = match.group(3)
        rewritten = resolve(inner)
        if rewritten is None:
            return match.group(0)
        if rewritten == inner:
            return match.group(0)
        return f"{match.group(1)}({rewritten})"

    converted = LINK_RE.sub(replace, converted)
    return converted, unresolved


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
    name = posixpath.basename(folder)
    return name.replace("-", " ").replace("_", " ").title()


def meta_plans(ledger: dict, manifest: dict) -> dict[str, dict]:
    folders: dict[str, dict] = {}
    for page in ledger["pages"]:
        folder = posixpath.dirname(page["output_path"])
        folders.setdefault(folder, {"index": None, "files": [], "write_order": {}})
        if posixpath.basename(page["output_path"]) == "index.mdx":
            folders[folder]["index"] = page
        else:
            folders[folder]["files"].append(page)
        folders[folder]["write_order"][page["doc_id"]] = page["write_order"]
    for folder in folders:
        folders[folder]["files"].sort(key=lambda p: (p["write_order"], p["source_path"]))

    def folder_order(folder: str) -> tuple[int, str]:
        """Meaningful order: a folder is ordered by its index document's
        manifest write_order, else by the smallest write_order among its
        pages, with the folder name as the deterministic tie-break."""
        info = folders.get(folder)
        if info is None:
            return (10**9, folder)
        if info["index"] is not None:
            return (info["index"]["write_order"], folder)
        return (min((p["write_order"] for p in info["files"]), default=10**9), folder)

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
            entries.append(((page["write_order"], stem), stem))
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
            raise ValueError(f"document has no frontmatter: {doc['source_path']}")
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
        content = public_frontmatter(page, provenance) + mdx_body
        target = stage_docs / doc["output_path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        anchors[doc["url"]] = heading_anchors(mdx_body)
        converted.append({"doc": doc["doc_id"], "url": doc["url"], "output": doc["output_path"], "unresolved": unresolved})
    return {"converted": converted, "assets_needed": sorted(assets_needed), "anchors": anchors}


def copy_assets(repo: Path, dashboard: Path, assets: list[str]) -> list[str]:
    copied = []
    for rel in assets:
        source = repo / rel
        if not source.is_file() or not rel.endswith(tuple(ASSET_EXTS)):
            continue
        if source.stat().st_size > ASSET_MAX_BYTES:
            continue
        target = dashboard / "public" / "docs-assets" / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        copied.append(rel)
    return copied


def swap_stage(dashboard: Path, stage_docs: Path, stage_meta: dict[str, dict]) -> None:
    content_dir = dashboard / "content"
    target = content_dir / "docs"
    if target.exists():
        shutil.rmtree(target)
    os.rename(stage_docs, target)
    for folder, meta in stage_meta.items():
        meta_path = content_dir / "docs" / meta["path"]
        meta_path.parent.mkdir(parents=True, exist_ok=True)
        meta_path.write_text(dump_json({"title": meta["title"], "pages": meta["pages"]}), encoding="utf-8")


def validate_build(repo: Path, manifest: dict, dashboard: Path) -> dict:
    docs = included_documents(repo, manifest)
    ledger = build_ledger(docs)
    errors: list[str] = []
    warnings: list[str] = []
    content_dir = dashboard / "content" / "docs"
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
                if not (dashboard / "public" / "docs-assets" / asset).is_file():
                    errors.append(f"missing asset in {page['output_path']}: {target}")
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
    sha = template_sha(template_dir)
    if not force and current.get("template_sha") == sha and (dashboard / "lib" / "shared.ts").is_file():
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


class ServeInterrupted(Exception):
    def __init__(self, signum: int):
        super().__init__(f"dashboard serve interrupted by signal {signum}")
        self.signum = signum


def wait_for_server(port: int, log_path: Path, timeout: int = 180, interrupted=None) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        signum = interrupted() if interrupted else None
        if signum:
            raise ServeInterrupted(signum)
        if server_up(port):
            return
        time.sleep(0.25)
    tail = ""
    if log_path.is_file():
        lines = log_path.read_text(encoding="utf-8", errors="replace").splitlines()
        tail = "\n".join(lines[-40:])
    raise ValueError(f"dashboard server did not start within {timeout}s; last log lines:\n{tail}")


def ensure_server(dashboard: Path, requested_port: int | None, interrupted=None) -> dict:
    state = load_state(dashboard)
    log_path = dashboard / "dev.log"
    signum = interrupted() if interrupted else None
    if signum:
        raise ServeInterrupted(signum)
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
        wait_for_server(port, log_path, interrupted=interrupted)
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
        signal_process_group(pid, signal.SIGTERM)
        deadline = time.time() + 3
        while process_group_alive(pid) and time.time() < deadline:
            time.sleep(0.05)
        if process_group_alive(pid):
            forced = signal_process_group(pid, signal.SIGKILL)
    state.pop("pid", None)
    state.pop("port", None)
    state.pop("url", None)
    save_state(dashboard, state)
    return {"stopped": stopped, "forced": forced}


def supervise_server(pid: int, interrupted) -> int | None:
    while process_group_alive(pid):
        signum = interrupted()
        if signum:
            return signum
        time.sleep(0.25)
    return None


def cmd_status(args: argparse.Namespace, dashboard: Path, manifest: dict, template_dir: Path) -> int:
    docs = included_documents(args.repo, manifest)
    state = load_state(dashboard)
    current_fp = fingerprint(args.repo, args.manifest, manifest, template_dir)
    running = False
    if state.get("pid") and isinstance(state.get("port"), int):
        running = pid_alive(state["pid"]) and server_up(state["port"])
    result = {
        "dashboard": str(dashboard),
        "exists": dashboard.is_dir(),
        "template_sha": state.get("template_sha"),
        "fingerprint": {
            "current": current_fp,
            "stored": state.get("fingerprint"),
            "match": state.get("fingerprint") == current_fp,
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
        print(f"exists: {result['exists']}  fingerprint match: {result['fingerprint']['match']}")
        print(f"server: {'running on ' + str(result['server']['url']) if result['server']['running'] else 'not running'}")
        print(f"included documents: {result['counts']['included_docs']}")
    return 0


def cmd_fingerprint(args: argparse.Namespace, manifest: dict, template_dir: Path) -> int:
    value = fingerprint(args.repo, args.manifest, manifest, template_dir)
    if args.json:
        print(dump_json({"fingerprint": value}))
    else:
        print(value)
    return 0


def cmd_metadata(args: argparse.Namespace, manifest: dict) -> int:
    report = reconcile_metadata(args.repo, manifest, dry_run=args.dry_run)
    if args.json:
        print(dump_json(report))
    else:
        print(f"reconciled: {report['counts']['reconciled']}  unchanged: {report['counts']['unchanged']}  errors: {report['counts']['errors']}")
        for entry in report["reconciled"]:
            print(f"  {entry['doc']}: fixed {', '.join(entry['fixed'])}")
        for entry in report["errors"]:
            print(f"  error {entry['doc']}: {entry['detail']}")
    return 1 if report["counts"]["errors"] else 0


def cmd_plan(args: argparse.Namespace, manifest: dict) -> int:
    result = plan(args.repo, manifest)
    if args.json:
        print(dump_json(result))
    else:
        for page in result["pages"]:
            print(f"  {page['doc_id']:<32} {page['source_path']:<48} -> {page['url']}")
        print(f"{len(result['pages'])} pages in {result['folder_count']} folders; {len(result['problems'])} problems")
        for problem in result["problems"]:
            print(f"  problem: {problem}")
    return 1 if result["problems"] else 0


def cmd_build(args: argparse.Namespace, dashboard: Path, manifest: dict, template_dir: Path) -> int:
    if not args.no_metadata:
        metadata_report = reconcile_metadata(args.repo, manifest)
        print(f"metadata: {metadata_report['counts']['reconciled']} reconciled, {metadata_report['counts']['unchanged']} unchanged")
    current_fp = fingerprint(args.repo, args.manifest, manifest, template_dir)
    state = load_state(dashboard)
    if not args.force and state.get("fingerprint") == current_fp and (dashboard / "content" / "docs" / "index.mdx").is_file():
        print("fingerprint unchanged: no conversion needed")
        if not (dashboard / "node_modules").is_dir() and not args.skip_install:
            ensure_dependencies(dashboard, args.repo)
        return 0
    scaffold_app(dashboard, template_dir, args.repo, manifest)
    docs = included_documents(args.repo, manifest)
    ledger = build_ledger(docs)
    route_plan = plan(args.repo, manifest)
    if route_plan["problems"]:
        for problem in route_plan["problems"]:
            print(f"problem: {problem}")
        print("route plan has errors; fix the manifest or document tree before building")
        return 1
    content_dir = dashboard / "content"
    staging = content_dir / ".staging"
    stage_docs = staging / "docs"
    if stage_docs.exists():
        shutil.rmtree(stage_docs)
    stage_docs.mkdir(parents=True, exist_ok=True)
    try:
        ledger["assets"] = collect_asset_map(args.repo)
        converted = convert_documents(args.repo, manifest, ledger, stage_docs)
        meta = meta_plans(ledger, manifest)
        swap_stage(dashboard, stage_docs, meta)
        if staging.exists():
            shutil.rmtree(staging)
        copied = copy_assets(args.repo, dashboard, converted["assets_needed"])
        new_state = dict(state)
        new_state.update({
            "schema": STATE_SCHEMA,
            "dashboard": str(dashboard.resolve()),
            "template_sha": template_sha(template_dir),
            "fingerprint": current_fp,
            "built_at": now_iso(),
        })
        save_state(dashboard, new_state)
    except Exception as exc:  # noqa: BLE001
        if staging.exists():
            shutil.rmtree(staging)
        raise
    print(f"converted {len(converted['converted'])} documents; copied {len(copied)} assets")
    if not args.skip_install:
        ensure_dependencies(dashboard, args.repo)
    print("build complete")
    return 0


def cmd_validate(args: argparse.Namespace, dashboard: Path, manifest: dict) -> int:
    result = validate_build(args.repo, manifest, dashboard)
    if args.json:
        print(dump_json(result))
    else:
        print(f"pages: {result['counts']['pages']}  meta files: {result['counts']['meta_files']}  ok: {result['ok']}")
        for error in result["errors"]:
            print(f"  error: {error}")
        for warning in result["warnings"]:
            print(f"  warning: {warning}")
    return 0 if result["ok"] else 1


def cmd_serve(args: argparse.Namespace, dashboard: Path) -> int:
    stop_signal = None
    watched = [signal.SIGINT, signal.SIGTERM]
    for name in ("SIGHUP", "SIGTSTP"):
        value = getattr(signal, name, None)
        if value is not None:
            watched.append(value)
    previous = {value: signal.getsignal(value) for value in watched}

    def request_stop(signum, _frame) -> None:
        nonlocal stop_signal
        if stop_signal is None:
            stop_signal = signum

    for value in watched:
        signal.signal(value, request_stop)

    try:
        result = ensure_server(dashboard, args.port, interrupted=lambda: stop_signal)
        print(f"dashboard: {result['url']} (reused={result['reused']})")
        print("server attached; press Ctrl+C or Ctrl+Z to stop")
        stop_signal = supervise_server(result["pid"], lambda: stop_signal)
    except ServeInterrupted as exc:
        stop_signal = exc.signum
    finally:
        for value, handler in previous.items():
            signal.signal(value, handler)
        stop_server(dashboard)

    if stop_signal is not None:
        print("dashboard server stopped")
        return 128 + stop_signal
    print("dashboard server exited unexpectedly")
    return 1


def cmd_stop(args: argparse.Namespace, dashboard: Path) -> int:
    result = stop_server(dashboard)
    print(f"stopped: {result['stopped']}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="dashboard", description="Docforge dashboard: metadata, conversion, validation, serving")
    parser.add_argument("--repo", default=".", help="repository root (default: current directory)")
    parser.add_argument("--manifest", default=None, help="manifest path (default: <repo>/.docforge/manifest.json)")
    parser.add_argument("--dashboard", default=None, help="dashboard directory (default: <repo>/.docforge/dashboard)")
    parser.add_argument("--json", action="store_true", help="JSON output")
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--repo", default=".", help="repository root (default: current directory)")
    common.add_argument("--manifest", default=None, help="manifest path (default: <repo>/.docforge/manifest.json)")
    common.add_argument("--dashboard", default=None, help="dashboard directory (default: <repo>/.docforge/dashboard)")
    common.add_argument("--json", action="store_true", help="JSON output")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("status", parents=[common], help="dashboard state and server status")
    sub.add_parser("fingerprint", parents=[common], help="print the current fingerprint")
    metadata = sub.add_parser("metadata", parents=[common], help="reconcile public id/title frontmatter from the manifest")
    metadata.add_argument("--dry-run", action="store_true", help="report only, do not write")
    sub.add_parser("plan", parents=[common], help="show the route ledger before building")
    build = sub.add_parser("build", parents=[common], help="scaffold, convert, and assemble the dashboard")
    build.add_argument("--force", action="store_true", help="rebuild even when the fingerprint is unchanged")
    build.add_argument("--skip-install", action="store_true", help="do not run npm install/ci")
    build.add_argument("--no-metadata", action="store_true", help="skip metadata reconciliation")
    sub.add_parser("validate", parents=[common], help="validate the built dashboard (links, coverage, assets)")
    serve = sub.add_parser("serve", parents=[common], help="start (or reuse) the local dev server")
    serve.add_argument("--port", type=int, default=0, help="port (default: auto)")
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
    template_dir = Path(__file__).resolve().parent / "template"
    if args.command in {"status", "fingerprint", "metadata", "plan", "build", "validate"}:
        try:
            manifest = load_manifest(manifest_path)
        except ValueError as exc:
            return fail(str(exc))
    else:
        manifest = {}
    try:
        if args.command == "status":
            return cmd_status(args, dashboard, manifest, template_dir)
        if args.command == "fingerprint":
            return cmd_fingerprint(args, manifest, template_dir)
        if args.command == "metadata":
            return cmd_metadata(args, manifest)
        if args.command == "plan":
            return cmd_plan(args, manifest)
        if args.command == "build":
            return cmd_build(args, dashboard, manifest, template_dir)
        if args.command == "validate":
            return cmd_validate(args, dashboard, manifest)
        if args.command == "serve":
            return cmd_serve(args, dashboard)
        if args.command == "stop":
            return cmd_stop(args, dashboard)
    except ValueError as exc:
        return fail(str(exc))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
