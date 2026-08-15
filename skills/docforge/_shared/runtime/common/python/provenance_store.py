#!/usr/bin/env python3
"""Folder-mirrored JSON sidecar store for Docforge document metadata.

When `project.provenance_storage` is `json` (the default), the public
frontmatter identity (id, title, description) and the private
`docforge_provenance` object live in one git-tracked JSON file per docs
folder under `.docforge/provenance/`, and the markdown files carry no
frontmatter at all. With `markdown` storage the legacy inline frontmatter
layout is kept. Both runtimes share this module so file moves, reads, and
writes stay byte-identical.
"""

from __future__ import annotations

import json
from pathlib import Path, PurePosixPath
from typing import Any

from runtime.common.python.provenance_frontmatter import (
    emit_document_frontmatter,
    parse_yaml_mapping,
    split_frontmatter,
)

SIDECAR_SCHEMA = "1.0"
STORAGE_JSON = "json"
STORAGE_MARKDOWN = "markdown"
SIDECAR_DIRNAME = "provenance"
PUBLIC_FIELDS = ("id", "title", "description")


class SidecarError(ValueError):
    """Raised when a sidecar file cannot be read or written."""


def storage_for(manifest: dict) -> str:
    """The project's provenance storage mode; json when unset (default)."""
    value = (manifest.get("project") or {}).get("provenance_storage")
    return value if value in {STORAGE_JSON, STORAGE_MARKDOWN} else STORAGE_JSON


def sidecar_root(repo: Path) -> Path:
    return repo / ".docforge" / SIDECAR_DIRNAME


def folder_of(doc_path: str) -> str:
    """POSIX folder path for a document; "" for repo-root documents."""
    parent = PurePosixPath(doc_path.replace("\\", "/")).parent
    folder = parent.as_posix()
    return "" if folder in ("", ".") else folder


def sidecar_path(repo: Path, folder: str) -> Path:
    """`.docforge/provenance/<folder>.json`; `root.json` for repo root."""
    name = f"{folder}.json" if folder else "root.json"
    return sidecar_root(repo) / name


def read_sidecar(repo: Path, folder: str) -> dict | None:
    """The sidecar object for a folder, or None when absent."""
    path = sidecar_path(repo, folder)
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SidecarError(f"invalid sidecar {path.relative_to(repo)}: {exc}") from exc
    if not isinstance(data, dict) or not isinstance(data.get("files"), dict):
        raise SidecarError(f"invalid sidecar shape: {path.relative_to(repo)}")
    return data


def write_sidecar(repo: Path, folder: str, data: dict) -> None:
    """Write a folder sidecar, creating `.docforge/provenance/` as needed."""
    path = sidecar_path(repo, folder)
    files = data.get("files") if isinstance(data, dict) else None
    if not isinstance(files, dict) or not files:
        if path.is_file():
            path.unlink()
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"schema": SIDECAR_SCHEMA, "folder": folder, "files": files}
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def file_name_of(doc_path: str) -> str:
    return PurePosixPath(doc_path.replace("\\", "/")).name


def entry_for(repo: Path, doc_path: str) -> dict | None:
    """The sidecar entry for one document, or None."""
    data = read_sidecar(repo, folder_of(doc_path))
    if data is None:
        return None
    entry = data["files"].get(file_name_of(doc_path))
    return entry if isinstance(entry, dict) else None


def write_entry(repo: Path, doc_path: str, entry: dict) -> None:
    """Merge one document's entry into its folder sidecar."""
    folder = folder_of(doc_path)
    name = file_name_of(doc_path)
    data = read_sidecar(repo, folder)
    files = dict(data["files"]) if data else {}
    files[name] = entry
    write_sidecar(repo, folder, {"files": files})


def remove_entry(repo: Path, doc_path: str) -> None:
    """Drop one document's entry, deleting the sidecar when it becomes empty."""
    folder = folder_of(doc_path)
    name = file_name_of(doc_path)
    data = read_sidecar(repo, folder)
    if not data or name not in data["files"]:
        return
    files = dict(data["files"])
    del files[name]
    write_sidecar(repo, folder, {"files": files})


def read_inline(text: str) -> tuple[str, dict | None]:
    """Parse a markdown file's full frontmatter mapping (id/title/description
    plus docforge_provenance) without interpreting schema state."""
    raw, _body, _end = split_frontmatter(text)
    if raw is None:
        return "missing", None
    try:
        data = parse_yaml_mapping(raw)
    except ValueError:
        return "unparseable", None
    if not isinstance(data, dict):
        return "missing", None
    return "ok", data


def read_doc_metadata(repo: Path, doc: dict, storage: str) -> dict:
    """Mode-aware read of one document's metadata.

    Returns {"state", "public", "provenance", "source"} where state is one
    of ok | missing | unparseable | inline and source is sidecar|markdown.
    In json mode a file whose inline frontmatter has not been migrated yet
    reports state `inline` so callers can trigger the move.
    """
    doc_path = doc.get("path", "")
    target = repo / doc_path
    if storage == STORAGE_JSON:
        entry = entry_for(repo, doc_path)
        if isinstance(entry, dict) and isinstance(entry.get("provenance"), dict):
            return {
                "state": "ok",
                "public": {key: entry.get(key) for key in PUBLIC_FIELDS},
                "provenance": entry["provenance"],
                "source": "sidecar",
            }
        if target.is_file():
            text = target.read_text(encoding="utf-8", errors="replace")
            state, data = read_inline(text)
            if state == "ok" and isinstance(data.get("docforge_provenance"), dict):
                return {
                    "state": "inline",
                    "public": {key: data.get(key) for key in PUBLIC_FIELDS},
                    "provenance": data["docforge_provenance"],
                    "source": "markdown",
                }
            if state == "unparseable":
                return {"state": "unparseable", "public": None, "provenance": None, "source": "markdown"}
        return {"state": "missing", "public": None, "provenance": None, "source": "sidecar"}
    if not target.is_file():
        return {"state": "missing", "public": None, "provenance": None, "source": "markdown"}
    text = target.read_text(encoding="utf-8", errors="replace")
    state, data = read_inline(text)
    if state == "unparseable":
        return {"state": "unparseable", "public": None, "provenance": None, "source": "markdown"}
    if state == "ok" and isinstance(data.get("docforge_provenance"), dict):
        return {
            "state": "ok",
            "public": {key: data.get(key) for key in PUBLIC_FIELDS},
            "provenance": data["docforge_provenance"],
            "source": "markdown",
        }
    return {"state": "missing", "public": None, "provenance": None, "source": "markdown"}


def public_from_manifest(doc: dict) -> dict:
    """Public identity (id/title/description) seeded from the manifest entry."""
    title = doc.get("title") or doc["id"].replace("-", " ").replace("_", " ").title()
    public: dict[str, Any] = {"id": doc["id"], "title": title}
    if doc.get("description"):
        public["description"] = doc["description"]
    return public


def move_inline_to_sidecar(repo: Path, doc: dict, storage: str) -> str:
    """Move a document's inline frontmatter into the folder sidecar and strip
    it from the markdown. No-op unless json storage and inline exists."""
    if storage != STORAGE_JSON:
        return "skip"
    doc_path = doc.get("path", "")
    target = repo / doc_path
    if not target.is_file():
        return "missing"
    text = target.read_text(encoding="utf-8", errors="replace")
    state, data = read_inline(text)
    if state == "unparseable":
        return "unparseable"
    if state == "missing" or not isinstance(data.get("docforge_provenance"), dict):
        return "no-frontmatter"
    public = {key: data.get(key) for key in PUBLIC_FIELDS if data.get(key)}
    if not public.get("id"):
        public["id"] = doc.get("id", "")
    if not public.get("title"):
        public["title"] = doc.get("title") or doc.get("id", "document").replace("-", " ").title()
    if not public.get("description") and doc.get("description"):
        public["description"] = doc["description"]
    entry = {key: value for key, value in public.items() if value}
    entry["provenance"] = data["docforge_provenance"]
    write_entry(repo, doc_path, entry)
    _raw, body, _end = split_frontmatter(text)
    target.write_text(body.lstrip("\n"), encoding="utf-8")
    return "moved"


def move_sidecar_to_inline(repo: Path, doc: dict) -> str:
    """Re-emit a sidecar entry as inline frontmatter and drop the entry."""
    doc_path = doc.get("path", "")
    entry = entry_for(repo, doc_path)
    if not isinstance(entry, dict):
        return "no-sidecar"
    public = {key: entry.get(key) for key in PUBLIC_FIELDS if entry.get(key)}
    title = public.get("title") or doc.get("title") or doc.get("id", "document")
    doc_id = public.get("id") or doc.get("id", "")
    description = public.get("description")
    frontmatter = emit_document_frontmatter(
        doc_id, title, entry["provenance"], description
    )
    target = repo / doc_path
    if target.is_file():
        text = target.read_text(encoding="utf-8", errors="replace")
        _raw, body, _end = split_frontmatter(text)
        content = frontmatter + body.lstrip("\n")
    else:
        content = frontmatter
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    remove_entry(repo, doc_path)
    return "moved"
