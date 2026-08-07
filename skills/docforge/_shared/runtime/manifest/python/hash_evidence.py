#!/usr/bin/env python3
"""Stamp git_blob / git_blob_normalized / range_blob for one provenance source.

The writing agent uses this to hash a cited file (and optionally a specific
line range) exactly the way `check_staleness.py` will later recompute it --
`git_blob` matches `git hash-object`; `git_blob_normalized` and `range_blob`
have no standard-tool equivalent, so both sides must share one implementation.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from runtime.common.python._util import fail
from runtime.common.python.evidence_hash import (
    normalized_blob_hash,
    range_blob_hash,
    raw_blob_hash,
)


def parse_range(value: str) -> tuple[int, int]:
    start_text, sep, end_text = value.partition("-")
    if not sep or not start_text.isdigit() or not end_text.isdigit():
        raise ValueError(f"invalid --range: {value!r} (expected <start>-<end>)")
    start, end = int(start_text), int(end_text)
    if start < 1 or end < start:
        raise ValueError(f"invalid --range: {value!r} (expected 1 <= start <= end)")
    return start, end


def hash_evidence(repo: Path, rel_path: str, span: tuple[int, int] | None) -> dict:
    if Path(rel_path).is_absolute() or ".." in Path(rel_path).parts:
        raise ValueError(f"path escapes repo: {rel_path}")
    target = (repo / rel_path).resolve()
    if repo.resolve() not in (target, *target.parents):
        raise ValueError(f"path escapes repo: {rel_path}")
    if not target.is_file():
        raise ValueError(f"file not found: {rel_path}")
    content = target.read_bytes()
    result: dict = {"git_blob": raw_blob_hash(content)}
    normalized = normalized_blob_hash(content)
    if normalized is not None:
        result["git_blob_normalized"] = normalized
    if span is not None:
        start, end = span
        scoped = range_blob_hash(content, start, end)
        if scoped is None:
            raise ValueError(
                f"cannot hash range {start}-{end} of {rel_path} "
                "(out of bounds or not valid UTF-8 text)"
            )
        result["evidence_range"] = {"start": str(start), "end": str(end)}
        result["range_blob"] = scoped
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--path", required=True, help="Repo-relative path to hash")
    parser.add_argument("--range", help="1-indexed inclusive line span, e.g. 10-20")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    if not args.repo.is_dir():
        return fail(f"not a directory: {args.repo}", 2)
    try:
        span = parse_range(args.range) if args.range else None
        result = hash_evidence(args.repo.resolve(), args.path, span)
    except ValueError as exc:
        return fail(str(exc), 2)
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"git_blob: {result['git_blob']}")
        if "git_blob_normalized" in result:
            print(f"git_blob_normalized: {result['git_blob_normalized']}")
        if "evidence_range" in result:
            print(f"evidence_range: {result['evidence_range']['start']}-{result['evidence_range']['end']}")
            print(f"range_blob: {result['range_blob']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
