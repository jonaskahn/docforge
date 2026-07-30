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


def load_manifest(
    path: Path,
    *,
    allowed_versions: Sequence[str] = ("3.1",),
    require_documents: bool = False,
    unsupported_hint: str = "run migrate_metadata.py for 3.0 manifests",
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


if __name__ == "__main__":
    raise SystemExit("error: _util.py is a shared module, not a CLI")
