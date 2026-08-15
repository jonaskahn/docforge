#!/usr/bin/env python3
"""Folder-mirrored JSON sidecar store for Docforge document metadata.

The public frontmatter identity (id, title, description) and the private
`docforge_provenance` object live in one git-tracked JSON file per docs folder
under `.docforge/provenance/`; generated markdown carries no frontmatter at
all. Both runtimes share this module so file moves, reads, and writes stay
byte-identical.

Documents written before the sidecar store still carry inline frontmatter.
This module reads that layout so `migrate_metadata` can move it, but nothing
writes it.
"""

from __future__ import annotations

import json
from pathlib import Path, PurePosixPath
from typing import Any

from runtime.common.python.provenance_frontmatter import (
    LEGACY_SCHEMA,
    SUPPORTED_SCHEMA_VERSIONS,
    parse_yaml_mapping,
    split_frontmatter,
)

SIDECAR_SCHEMA = "1.0"
STORAGE_JSON = "json"
SIDECAR_DIRNAME = "provenance"
PUBLIC_FIELDS = ("id", "title", "description")


class SidecarError(ValueError):
    """Raised when a sidecar file cannot be read or written."""


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
    plus docforge_provenance) without interpreting schema state.

    A schema-1.0-era document may carry JSON frontmatter rather than
    restricted YAML — `parse_frontmatter` in `provenance_frontmatter.py`
    already special-cases this; mirror it here so a document without a
    sidecar entry is classified the same way regardless of which reader
    resolves it."""
    raw, _body, _end = split_frontmatter(text)
    if raw is None:
        return "missing", None
    stripped = raw.lstrip()
    if stripped.startswith("{"):
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return "unparseable", None
    else:
        try:
            data = parse_yaml_mapping(raw)
        except ValueError:
            return "unparseable", None
    if not isinstance(data, dict):
        return "missing", None
    return "ok", data


def schema_state(provenance: Any) -> str:
    """Explicit classification of a provenance object's schema.

    `ok` — current schema (2.0/2.1, no `tool_version`);
    `legacy` — no `schema` key at all (pre-schema shape);
    `obsolete` — schema 1.0, `tool_version`, or an unsupported schema;
    `missing` — not a provenance object. Detection is always on — there is
    no opt-in/opt-out: callers see the old-schema state explicitly and must
    migrate before any move.
    """
    if not isinstance(provenance, dict) or not provenance:
        return "missing"
    if "schema" not in provenance:
        return "legacy"
    if provenance["schema"] not in SUPPORTED_SCHEMA_VERSIONS or "tool_version" in provenance:
        return "obsolete"
    return "ok"


def read_doc_metadata(repo: Path, doc: dict) -> dict:
    """Read one document's metadata, sidecar first.

    Returns {"state", "public", "provenance", "source"}. State is explicit:
    `ok` (current schema, in the sidecar), `inline` (current-schema
    frontmatter on a document not yet migrated), `legacy` (schema-less
    provenance), `obsolete` (schema 1.0 / tool_version / unsupported schema),
    `missing`, or `unparseable`. Old-schema metadata is never folded into `ok`
    and is never silently moved.
    """
    doc_path = doc.get("path", "")
    target = repo / doc_path
    entry = entry_for(repo, doc_path)
    if isinstance(entry, dict) and isinstance(entry.get("provenance"), dict):
        return {
            "state": schema_state(entry["provenance"]),
            "public": {key: entry.get(key) for key in PUBLIC_FIELDS},
            "provenance": entry["provenance"],
            "source": "sidecar",
        }
    # No sidecar entry: the document may predate the store and still carry
    # frontmatter. Report that explicitly so migration can move it.
    if target.is_file():
        text = target.read_text(encoding="utf-8", errors="replace")
        state, data = read_inline(text)
        if state == "ok" and isinstance(data.get("docforge_provenance"), dict):
            schema = schema_state(data["docforge_provenance"])
            return {
                "state": "inline" if schema == "ok" else schema,
                "public": {key: data.get(key) for key in PUBLIC_FIELDS},
                "provenance": data["docforge_provenance"],
                "source": "markdown",
            }
        if state == "unparseable":
            return {"state": "unparseable", "public": None, "provenance": None, "source": "markdown"}
    return {"state": "missing", "public": None, "provenance": None, "source": "sidecar"}


def public_from_manifest(doc: dict) -> dict:
    """Public identity (id/title/description) seeded from the manifest entry."""
    title = doc.get("title") or doc["id"].replace("-", " ").replace("_", " ").title()
    public: dict[str, Any] = {"id": doc["id"], "title": title}
    if doc.get("description"):
        public["description"] = doc["description"]
    return public


def move_inline_to_sidecar(repo: Path, doc: dict) -> str:
    """Move a document's inline frontmatter into the folder sidecar and strip
    it from the markdown. Only current-schema provenance moves — old-schema
    metadata is reported explicitly (`legacy-schema` / `obsolete-schema`) and
    left untouched for migrate_metadata to convert first."""
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
    schema = schema_state(data["docforge_provenance"])
    if schema == "legacy":
        return "legacy-schema"
    if schema == "obsolete":
        return "obsolete-schema"
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
