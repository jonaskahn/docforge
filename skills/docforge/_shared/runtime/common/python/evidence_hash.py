"""Shared evidence hashing: raw git-blob hashes plus normalized and
line-range-scoped variants used to classify a cited source as fresh,
cosmetically drifted (whitespace/EOL-only, or the cited span is untouched),
or genuinely stale. Standard library only, no git dependency."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any

from runtime.common.python.provenance_frontmatter import BLOB

_LINE_SPLIT = re.compile(r"\r\n|\r|\n")
_RANGE_NUM = re.compile(r"^[1-9][0-9]*$")


def _decode_lines(content: bytes) -> list[str] | None:
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        return None
    if text == "":
        return []
    lines = _LINE_SPLIT.split(text)
    if lines and lines[-1] == "" and text[-1:] in ("\n", "\r"):
        lines.pop()
    return lines


def raw_blob_hash(content: bytes) -> str:
    header = f"blob {len(content)}\0".encode("ascii")
    return hashlib.sha1(header + content).hexdigest()


def git_blob_for_path(path: Path) -> str | None:
    if not path.is_file():
        return None
    return raw_blob_hash(path.read_bytes())


def normalize_text_bytes(content: bytes) -> bytes | None:
    """CRLF/CR->LF, strip trailing whitespace per line, drop trailing blank
    lines at EOF. Deliberately does not touch comments, indentation, or
    internal blank-line runs -- conservative enough to stay safe across every
    language Docforge might cite."""
    lines = _decode_lines(content)
    if lines is None:
        return None
    trimmed = [line.rstrip(" \t") for line in lines]
    while trimmed and trimmed[-1] == "":
        trimmed.pop()
    if not trimmed:
        return b""
    return ("\n".join(trimmed) + "\n").encode("utf-8")


def normalized_blob_hash(content: bytes) -> str | None:
    normalized = normalize_text_bytes(content)
    return None if normalized is None else raw_blob_hash(normalized)


def line_count(content: bytes) -> int | None:
    lines = _decode_lines(content)
    return None if lines is None else len(lines)


def range_blob_hash(content: bytes, start: int, end: int) -> str | None:
    """Hash of the 1-indexed, inclusive line slice [start, end]."""
    lines = _decode_lines(content)
    if lines is None or start < 1 or end < start or end > len(lines):
        return None
    return raw_blob_hash("\n".join(lines[start - 1:end]).encode("utf-8"))


def _valid_range(evidence_range: Any, range_blob: Any) -> tuple[int, int] | None:
    if (
        isinstance(evidence_range, dict)
        and isinstance(evidence_range.get("start"), str) and _RANGE_NUM.match(evidence_range["start"])
        and isinstance(evidence_range.get("end"), str) and _RANGE_NUM.match(evidence_range["end"])
        and int(evidence_range["end"]) >= int(evidence_range["start"])
        and isinstance(range_blob, str) and BLOB.fullmatch(range_blob)
    ):
        return int(evidence_range["start"]), int(evidence_range["end"])
    return None


def classify_source(source: dict[str, Any], current_bytes: bytes | None) -> str:
    """Classify a provenance source given the CURRENT bytes of its cited path.

    Caller must validate the recorded `git_blob` is a well-formed 40-hex
    string before calling this -- a malformed/missing recorded blob is a
    NO_BLOB data-quality defect, never eligible for downgrade. Returns one of
    "missing", "fresh", "cosmetic", "stale", checked in that precedence:
    raw match (cheapest) -> range-scoped match (most specific) ->
    normalized match -> otherwise genuinely stale.
    """
    if current_bytes is None:
        return "missing"
    if raw_blob_hash(current_bytes) == source.get("git_blob"):
        return "fresh"
    span = _valid_range(source.get("evidence_range"), source.get("range_blob"))
    if span is not None:
        current_range = range_blob_hash(current_bytes, *span)
        if current_range is not None and current_range == source["range_blob"]:
            return "cosmetic"
    normalized = source.get("git_blob_normalized")
    if isinstance(normalized, str) and BLOB.fullmatch(normalized):
        current_normalized = normalized_blob_hash(current_bytes)
        if current_normalized is not None and current_normalized == normalized:
            return "cosmetic"
    return "stale"
