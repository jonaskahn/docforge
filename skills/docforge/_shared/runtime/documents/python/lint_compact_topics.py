#!/usr/bin/env python3
"""Cross-topic isolation lint for the compact coding-agent reference.

The compact contract promises that every topic section is self-contained:
facts a topic needs are repeated within it rather than pointed at another
section. This linter rejects cross-topic mentions and pointer phrases.

Usage:
    python lint_compact_topics.py --file docs/agents.md [--json]

Exit 0 when no defects exist, 1 for defects, and 2 for usage or IO errors.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

H2_RE = re.compile(r"^##\s+(.+?)\s*#*\s*$")
POINTER_RE = re.compile(
    r"\b(?:see (?:also )?|as described in|refer to|per the)\b",
    re.IGNORECASE,
)


def lint_compact_topics(path: Path) -> dict:
    text = path.read_text(encoding="utf-8", errors="ignore")
    lines = text.split("\n")

    sections: list[tuple[str, int, int]] = []  # (title, start_line_1based, end_index)
    headings: list[tuple[int, str]] = []
    for index, line in enumerate(lines):
        match = H2_RE.match(line)
        if match:
            headings.append((index, match.group(1).strip()))
    sections = [
        {
            "title": title,
            "line": index + 1,
            "start": index + 1,
            "end": headings[position + 1][0] if position + 1 < len(headings) else len(lines),
        }
        for position, (index, title) in enumerate(headings)
    ]

    defects: list[dict] = []
    titles = [item["title"] for item in sections]
    for position, item in enumerate(sections):
        others = [title for other_position, title in enumerate(titles) if other_position != position]
        body = lines[item["start"]:item["end"]]
        for offset, line in enumerate(body):
            number = item["start"] + offset + 1
            if H2_RE.match(line):
                continue
            for other in others:
                pattern = r"\b" + re.escape(other) + r"\b"
                if re.search(pattern, line):
                    defects.append({
                        "kind": "cross-topic-mention",
                        "line": number,
                        "detail": f"{item['title']} mentions {other}",
                    })
            if POINTER_RE.search(line):
                defects.append({
                    "kind": "cross-topic-pointer",
                    "line": number,
                    "detail": line.strip()[:80],
                })
    return {"file": str(path), "defects": defects}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--file", required=True, type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    if not args.file.is_file():
        print(f"error: not a file: {args.file}", file=sys.stderr)
        return 2
    result = lint_compact_topics(args.file)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        if not result["defects"]:
            print(f"CLEAN    {result['file']}")
        for defect in result["defects"]:
            print(f"DEFECT   {result['file']}:{defect['line']}  {defect['kind']}: {defect['detail']}")
    return 1 if result["defects"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
