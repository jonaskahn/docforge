#!/usr/bin/env python3
"""Mechanical rubric check for generated AGENTS.md and CLAUDE.md kernels.

The kernel must stay concise and self-contained: required operating sections,
verified commands, hard safety boundaries, and no documentation references.
Run this in place of the generic document linter for an ``agents-kernel``
output.

Usage:
    python lint_agents_kernel.py --file AGENTS.md [--json]

Exit 0 when no defects exist, 1 for defects, and 2 for usage or IO errors.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path, PurePosixPath

HEADING_RE = re.compile(r"^(#{1,6})\s+(.*\S)\s*$")
H2_RE = re.compile(r"^##\s+(.+?)\s*#*\s*$")
FENCE_MARKER_RE = re.compile(r"^\s*(`{3,}|~{3,})")
BARE_URL_RE = re.compile(r"https?://")
RAW_URL_TOKEN_RE = re.compile(r"\bhttps?://[^\s<>)\]\"']+")
MARKDOWN_LINK_RE = re.compile(r"!?\[([^\]\n]*)\]\(([^)\n]*)\)")
AT_IMPORT_RE = re.compile(
    r"(?<![\w@])@((?:(?:\.{1,2}/|/)?[\w.~+-]+)(?:/[\w.~+-]+)*/?(?:#[\w.~:-]+)?)"
)
DOC_PATH_RE = re.compile(
    r"(?<![\w@])((?:(?:\.{1,2}/|/)?(?:[\w.~+-]+/)*[\w.~+-]+\."
    r"(?:md|mdx|markdown|rst|adoc|asciidoc)(?:#[\w.~:-]+)?|docs/[\w.~+/-]*))"
    r"(?![\w./-])",
    re.IGNORECASE,
)
DOCUMENT_SUFFIXES = {".md", ".mdx", ".markdown", ".rst", ".adoc", ".asciidoc"}
REQUIRED_SECTIONS = (
    "Commands",
    "Repository map",
    "Precedence",
    "Boundaries",
    "Validation",
)
SECTION_ORDER = (
    "Commands",
    "Repository map",
    "Precedence",
    "Boundaries",
    "Conventions",
    "Validation",
)
MAX_NONBLANK_LINES = 80
LINE_WARNING_AT = 68
GUARD_RE = re.compile(r"\b(?:never|must not|do not|without)\b", re.IGNORECASE)
SECRET_RE = re.compile(r"(?:\b(?:secret|credential)\w*\b|\.env\b)", re.IGNORECASE)
VALIDATION_ACTION_RE = re.compile(r"\b(?:disable|skip|bypass|remove)\w*\b", re.IGNORECASE)
VALIDATION_TARGET_RE = re.compile(r"\b(?:test|validation|check)\w*\b", re.IGNORECASE)
DESTRUCTIVE_RE = re.compile(r"\bdestructive\b", re.IGNORECASE)
APPROVAL_RE = re.compile(r"\b(?:approval|permission|ask)\w*\b", re.IGNORECASE)


def _clean_reference(raw: str) -> str:
    return raw.strip().strip("`\"'<>").rstrip(".,;:!?")


def _link_target(raw: str) -> str:
    value = raw.strip()
    if value.startswith("<") and ">" in value:
        return value[1:value.index(">")]
    return value.split(maxsplit=1)[0] if value else ""


def _looks_like_document_reference(raw: str) -> bool:
    value = _clean_reference(raw).split("#", 1)[0].split("?", 1)[0].rstrip("/")
    return (
        value.startswith("docs/")
        or PurePosixPath(value).suffix.lower() in DOCUMENT_SUFFIXES
    )


def _mask_spans(line: str, spans: list[tuple[int, int]]) -> str:
    chars = list(line)
    for start, end in spans:
        chars[start:end] = " " * (end - start)
    return "".join(chars)


def _fence_blocks(lines: list[str]) -> tuple[list[dict], set[int]]:
    blocks: list[dict] = []
    protected: set[int] = set()
    current: dict | None = None
    for index, line in enumerate(lines):
        if current is not None:
            protected.add(index)
            marker = current["marker"]
            if re.match(rf"^\s*{re.escape(marker[0])}{{{len(marker)},}}\s*$", line):
                current["end"] = index
                current = None
            continue
        match = FENCE_MARKER_RE.match(line)
        if match:
            current = {"start": index, "end": None, "marker": match.group(1)}
            blocks.append(current)
            protected.add(index)
    return blocks, protected


def _sections(lines: list[str], protected: set[int], end: int) -> list[dict]:
    headings: list[tuple[int, str]] = []
    for index, line in enumerate(lines[:end]):
        if index in protected:
            continue
        match = H2_RE.match(line)
        if match:
            headings.append((index, match.group(1).strip()))
    return [
        {
            "title": title,
            "line": index + 1,
            "start": index + 1,
            "end": headings[position + 1][0] if position + 1 < len(headings) else end,
        }
        for position, (index, title) in enumerate(headings)
    ]


def _canonical_title(title: str) -> str | None:
    by_name = {name.casefold(): name for name in SECTION_ORDER}
    return by_name.get(title.casefold())


def _section(sections: list[dict], title: str) -> dict | None:
    return next(
        (item for item in sections if item["title"].casefold() == title.casefold()),
        None,
    )


def _document_reference_defects(lines: list[str]) -> list[dict]:
    """Reject references rather than treating existing targets as valid."""
    defects: list[dict] = []
    for number, line in enumerate(lines, 1):
        link_spans: list[tuple[int, int]] = []
        for match in MARKDOWN_LINK_RE.finditer(line):
            target = _link_target(match.group(2)) or "<empty>"
            defects.append({
                "kind": "doc-reference",
                "line": number,
                "detail": f"markdown-link: {target}",
            })
            link_spans.append(match.span())
        working = _mask_spans(line, link_spans)

        url_spans = [match.span() for match in RAW_URL_TOKEN_RE.finditer(working)]
        working = _mask_spans(working, url_spans)

        import_spans: list[tuple[int, int]] = []
        for match in AT_IMPORT_RE.finditer(working):
            target = match.group(1)
            if _looks_like_document_reference(target):
                defects.append({
                    "kind": "doc-reference",
                    "line": number,
                    "detail": f"at-import: @{_clean_reference(target)}",
                })
                import_spans.append(match.span())
        working = _mask_spans(working, import_spans)

        for match in DOC_PATH_RE.finditer(working):
            defects.append({
                "kind": "doc-reference",
                "line": number,
                "detail": f"bare-path: {_clean_reference(match.group(1))}",
            })
    return defects


def _required_section_defects(sections: list[dict]) -> list[dict]:
    defects: list[dict] = []
    for title in REQUIRED_SECTIONS:
        matches = [
            item for item in sections
            if item["title"].casefold() == title.casefold()
        ]
        if not matches:
            defects.append({
                "kind": "missing-section",
                "line": 0,
                "detail": f"missing required section: {title}",
            })
        for duplicate in matches[1:]:
            defects.append({
                "kind": "duplicate-section",
                "line": duplicate["line"],
                "detail": title,
            })

    ordered = [
        (item, _canonical_title(item["title"]))
        for item in sections
        if _canonical_title(item["title"]) is not None
    ]
    positions = [SECTION_ORDER.index(canonical) for _item, canonical in ordered]
    for index in range(1, len(positions)):
        if positions[index] < positions[index - 1]:
            defects.append({
                "kind": "section-order",
                "line": ordered[index][0]["line"],
                "detail": "expected: " + ", ".join(SECTION_ORDER),
            })
            break
    return defects


def _command_defects(lines: list[str], sections: list[dict], blocks: list[dict]) -> list[dict]:
    commands = _section(sections, "Commands")
    if commands is None:
        return []
    command_blocks = [
        block for block in blocks
        if commands["start"] <= block["start"] < commands["end"]
    ]
    if not command_blocks:
        return [{
            "kind": "missing-command-block",
            "line": commands["line"],
            "detail": "Commands must contain a fenced block",
        }]
    block = command_blocks[0]
    if block["end"] is None:
        return []
    commands_in_block = [
        line.strip()
        for line in lines[block["start"] + 1:block["end"]]
        if line.strip()
        and not line.lstrip().startswith("#")
        and "{{" not in line
        and "TODO(" not in line
    ]
    if commands_in_block:
        return []
    return [{
        "kind": "empty-command-block",
        "line": block["start"] + 1,
        "detail": "Commands must contain at least one concrete command",
    }]


def _safety_defects(lines: list[str], sections: list[dict]) -> list[dict]:
    boundaries = _section(sections, "Boundaries")
    if boundaries is None:
        return []
    body = lines[boundaries["start"]:boundaries["end"]]
    checks = {
        "secrets": any(GUARD_RE.search(line) and SECRET_RE.search(line) for line in body),
        "validation": any(
            GUARD_RE.search(line)
            and VALIDATION_ACTION_RE.search(line)
            and VALIDATION_TARGET_RE.search(line)
            for line in body
        ),
        "destructive commands": any(
            DESTRUCTIVE_RE.search(line) and APPROVAL_RE.search(line)
            for line in body
        ),
    }
    return [
        {
            "kind": "missing-safety-rule",
            "line": boundaries["line"],
            "detail": f"Boundaries must cover {name}",
        }
        for name, present in checks.items()
        if not present
    ]


def lint_agents_kernel(path: Path, repo: Path | None = None) -> dict:
    # Retained for API compatibility. References are never resolved against
    # disk now that every document reference is a defect.
    _ = repo
    text = path.read_text(encoding="utf-8", errors="ignore")
    lines = text.split("\n")
    content_end = len(lines)
    while content_end > 0 and not lines[content_end - 1].strip():
        content_end -= 1

    defects: list[dict] = []
    warnings: list[dict] = []
    nonblank_lines = [
        index + 1 for index, line in enumerate(lines[:content_end]) if line.strip()
    ]
    nonblank_count = len(nonblank_lines)
    if nonblank_count > MAX_NONBLANK_LINES:
        defects.append({
            "kind": "line-cap",
            "line": nonblank_lines[MAX_NONBLANK_LINES],
            "detail": f"{nonblank_count} nonblank lines, cap is {MAX_NONBLANK_LINES}",
        })
    elif nonblank_count >= LINE_WARNING_AT:
        warnings.append({
            "kind": "line-cap-warning",
            "line": nonblank_lines[-1],
            "detail": (
                f"{nonblank_count} nonblank lines, approaching the "
                f"{MAX_NONBLANK_LINES}-line cap"
            ),
        })

    if not lines or not lines[0].startswith("# "):
        defects.append({
            "kind": "opening-shape",
            "line": 1,
            "detail": "line 1 must be a level-1 heading",
        })

    blocks, protected = _fence_blocks(lines[:content_end])
    sections = _sections(lines, protected, content_end)
    first_h2 = sections[0]["line"] - 1 if sections else content_end
    preamble = lines[1:first_h2]
    if not any(
        line.strip()
        and not HEADING_RE.match(line)
        and not line.lstrip().startswith("<!--")
        for line in preamble
    ):
        defects.append({
            "kind": "opening-shape",
            "line": 2,
            "detail": "no description prose between the title and first section",
        })

    defects.extend(_required_section_defects(sections))
    defects.extend(_command_defects(lines, sections, blocks))
    defects.extend(_safety_defects(lines, sections))

    if len(blocks) > 1:
        defects.append({
            "kind": "too-many-code-blocks",
            "line": blocks[1]["start"] + 1,
            "detail": f"{len(blocks)} fenced blocks, max 1",
        })
    for block in blocks:
        if block["end"] is None:
            defects.append({
                "kind": "unclosed-code-block",
                "line": block["start"] + 1,
                "detail": "fenced block is not closed",
            })

    if not any("<!--" in line for line in lines[:10]):
        defects.append({
            "kind": "missing-provenance",
            "line": 0,
            "detail": "no HTML-comment provenance in first 10 lines",
        })

    for index, line in enumerate(lines):
        without_links = _mask_spans(
            line, [match.span() for match in MARKDOWN_LINK_RE.finditer(line)]
        )
        if BARE_URL_RE.search(without_links):
            defects.append({
                "kind": "bare-url",
                "line": index + 1,
                "detail": line.strip(),
            })

    defects.extend(_document_reference_defects(lines))
    return {"file": str(path), "defects": defects, "warnings": warnings}


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--file", required=True, type=Path, help="AGENTS.md or CLAUDE.md")
    parser.add_argument(
        "--repo",
        type=Path,
        default=Path("."),
        help="accepted for compatibility; document references are always rejected",
    )
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = parser.parse_args()

    if not args.file.is_file():
        print(f"error: not a file: {args.file}", file=sys.stderr)
        return 2

    result = lint_agents_kernel(args.file, args.repo)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        if not result["defects"]:
            print(f"CLEAN    {result['file']}")
        for defect in result["defects"]:
            location = f":{defect['line']}" if defect["line"] else ""
            print(
                f"DEFECT   {result['file']}{location}  "
                f"{defect['kind']}: {defect['detail']}"
            )
        for warning in result["warnings"]:
            location = f":{warning['line']}" if warning["line"] else ""
            print(
                f"WARNING  {result['file']}{location}  "
                f"{warning['kind']}: {warning['detail']}"
            )
    return 1 if result["defects"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
