#!/usr/bin/env python3
"""Shared stdlib helpers for Docforge scripts. Not a public CLI."""

from __future__ import annotations

import json
import sys
from collections.abc import Sequence
from pathlib import Path


def fail(message: str, code: int = 1) -> int:
    print(f"error: {message}", file=sys.stderr)
    return code


def read_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise ValueError(f"file not found: {path}") from error
    except json.JSONDecodeError as error:
        raise ValueError(f"invalid JSON in {path}: {error}") from error
    if not isinstance(value, dict):
        raise ValueError(f"expected a JSON object: {path}")
    return value


def dump_json(value: object) -> str:
    return json.dumps(value, indent=2, ensure_ascii=False) + "\n"


import shutil


DOCFORGE_GITIGNORE_RULES: list[str] = [
    "# Ephemeral run state and scratch space for Docforge",
    "tmp/",
    "audits/",
    "scratch/",
    "backups/",
    "cache/",
    "obsolete/",
    "*.tmp",
    "*.log",
]


def ensure_docforge_gitignore(docforge_dir: Path) -> Path:
    """Create `docforge_dir` (.docforge) if needed and drop/update `.docforge/.gitignore`
    containing standard ignore rules so ephemeral state (tmp/, audits/, scratch/)
    is never committed, while persistent files (manifest.json, flow-index.json)
    stay tracked in git history."""
    docforge_dir.mkdir(parents=True, exist_ok=True)
    gitignore = docforge_dir / ".gitignore"
    if not gitignore.is_file():
        gitignore.write_text("\n".join(DOCFORGE_GITIGNORE_RULES) + "\n", encoding="utf-8")
    else:
        existing_lines = gitignore.read_text(encoding="utf-8").splitlines()
        missing = [
            rule
            for rule in DOCFORGE_GITIGNORE_RULES
            if not rule.startswith("#") and rule not in existing_lines
        ]
        if missing:
            content = gitignore.read_text(encoding="utf-8")
            suffix = "" if not content or content.endswith("\n") else "\n"
            gitignore.write_text(content + suffix + "\n".join(missing) + "\n", encoding="utf-8")
    return gitignore


def finish_docforge(docforge_dir: Path, clean_tmp: bool = True) -> dict:
    """Finish docforge process by ensuring .gitignore is present and cleaning up
    ephemeral run state inside .docforge (tmp/, scratch/). Returns status summary."""
    ensure_docforge_gitignore(docforge_dir)
    cleaned = []
    if clean_tmp:
        for folder_name in ("tmp", "scratch"):
            folder = docforge_dir / folder_name
            if folder.is_dir():
                for item in folder.iterdir():
                    if item.name == ".gitignore":
                        continue
                    if item.is_dir():
                        shutil.rmtree(item)
                    else:
                        item.unlink()
                cleaned.append(folder_name)
    return {
        "docforge_dir": str(docforge_dir),
        "gitignore_ensured": True,
        "cleaned_dirs": cleaned,
    }


def ensure_gitignored_dir(path: Path) -> Path:
    """Create `path` if needed and drop a `.gitignore` containing '*' inside
    it so its contents are never committed, in whichever repo Docforge is
    documenting. Idempotent."""
    path.mkdir(parents=True, exist_ok=True)
    if path.name in ("tmp", "audits", "scratch", "obsolete") and path.parent.name == ".docforge":
        ensure_docforge_gitignore(path.parent)
    gitignore = path / ".gitignore"
    if not gitignore.is_file():
        gitignore.write_text("*\n", encoding="utf-8")
    return gitignore


def load_manifest(
    path: Path,
    *,
    allowed_versions: Sequence[str] = ("3.9", "3.8", "3.7", "3.6", "3.5", "3.4", "3.3", "3.2", "3.1"),
    require_documents: bool = False,
    unsupported_hint: str = "run migrate_metadata.py to re-register legacy manifests",
) -> dict:
    if not path.is_file():
        raise ValueError(f"manifest not found: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    version = data.get("version")
    versions_text = " or ".join(allowed_versions)
    if version not in allowed_versions or (
        require_documents and not isinstance(data.get("documents"), list)
    ):
        raise ValueError(
            f"manifest must use version {versions_text}: {path}; {unsupported_hint}"
        )
    return data


def unmanaged_paths(manifest: dict) -> set[str]:
    """Paths the user decided to keep self-managed: never tracked by Docforge,
    never re-asked, updatable in place without ownership.

    Reads `project.unmanaged_docs` (`[{path, decided_at}]`)."""
    project = manifest.get("project")
    if not isinstance(project, dict):
        return set()
    entries = project.get("unmanaged_docs")
    if not isinstance(entries, list):
        return set()
    return {
        str(entry["path"])
        for entry in entries
        if isinstance(entry, dict) and isinstance(entry.get("path"), str) and entry["path"]
    }


if __name__ == "__main__":
    raise SystemExit("error: _util.py is a shared module, not a CLI")
