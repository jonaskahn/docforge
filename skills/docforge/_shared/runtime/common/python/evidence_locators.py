"""Validate immutable implementation evidence locators in generated Markdown."""

from __future__ import annotations

import re
from pathlib import Path

from runtime.common.python.provenance_frontmatter import parse_frontmatter
from runtime.common.python.evidence_hash import line_count, range_blob_hash, raw_blob_hash

LOCATOR_RE = re.compile(r"(?P<path>[A-Za-z0-9][A-Za-z0-9_./-]*)#L(?P<start>[1-9]\d*)-L(?P<end>[1-9]\d*) @ (?P<blob>[0-9a-f]{40})")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*\S)\s*$")


def _anchor(value: str) -> str:
    return re.sub(r"[\s-]+", "-", re.sub(r"[^\w\s-]", "", value.lower()).strip()).strip("-")


def _root(path: Path) -> Path:
    for parent in [path.parent, *path.parents]:
        if (parent / ".git").exists() or (parent / ".docforge").exists():
            return parent
    return path.parent


def _outside_fences(text: str) -> list[tuple[int, str]]:
    lines: list[tuple[int, str]] = []
    fence = False
    marker = ""
    for number, line in enumerate(text.splitlines(), 1):
        match = re.match(r"^\s*(`{3,})", line)
        if match:
            if not fence:
                fence, marker = True, match.group(1)
            elif match.group(1) == marker:
                fence, marker = False, ""
            continue
        if not fence:
            lines.append((number, line))
    return lines


def validate_locators(document: Path, text: str | None = None) -> list[dict]:
    """Return structured locator defects without broadening provenance 2.0."""
    text = document.read_text(encoding="utf-8", errors="replace") if text is None else text
    document = document.resolve()
    state, provenance, body_start = parse_frontmatter(text)
    if state != "ok" or not isinstance(provenance, dict):
        return []
    body = text[body_start:]
    body_line0 = text[:body_start].count("\n")
    headings: list[tuple[int, str]] = [
        (body_line0 + index, _anchor(match.group(2)))
        for index, line in enumerate(body.splitlines(), 1)
        if (match := HEADING_RE.match(line))
    ]
    source_pairs = {
        section.get("id"): {
            (source.get("path"), source.get("git_blob"))
            for source in section.get("sources", []) if isinstance(source, dict)
        }
        for section in provenance.get("sections", []) if isinstance(section, dict)
    }
    root = _root(document)
    defects: list[dict] = []
    for line_number, line in _outside_fences(text):
        for match in LOCATOR_RE.finditer(line):
            rel, start, end, digest = match.group("path"), int(match.group("start")), int(match.group("end")), match.group("blob")
            if ".." in Path(rel).parts or Path(rel).is_absolute():
                defects.append({"kind": "evidence path escape", "line": line_number, "detail": rel})
                continue
            target = (root / rel).resolve()
            if not target.is_file() or root not in [target, *target.parents]:
                defects.append({"kind": "evidence source missing", "line": line_number, "detail": rel})
                continue
            actual = target.read_bytes()
            whole_file = raw_blob_hash(actual)
            scoped = range_blob_hash(actual, start, end)
            if digest != whole_file and digest != scoped:
                defects.append({"kind": "stale evidence blob", "line": line_number, "detail": rel})
            count = line_count(actual)
            if end < start or count is None or end > count:
                defects.append({"kind": "invalid evidence range", "line": line_number, "detail": f"{rel}#L{start}-L{end}"})
            heading = next((anchor for heading_line, anchor in reversed(headings) if heading_line <= line_number), None)
            if heading is None:
                defects.append({"kind": "unknown evidence heading", "line": line_number, "detail": rel})
            elif (rel, digest) not in source_pairs.get(heading, set()):
                defects.append({"kind": "evidence provenance mismatch", "line": line_number, "detail": rel})
    return defects
