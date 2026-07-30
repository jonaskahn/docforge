#!/usr/bin/env python3
"""
lint_agents_kernel.py — mechanical rubric check for the coding-agents audience.

Runs the format-specific checks scripts/lint_document.py has no concept of: the
100-line cap, the 7-numbered-section shape, the tagline/test-sentence convention,
and dangling `@docs/agents/...` references. Run alongside lint_document.py, which
still covers this file's generic checks (scaffold markers, empty headings, dead
`[](...)`  links, unlinked mentions) — this script never replaces it.

Checks, for the single AGENTS.md-shaped file given:
  * line count <= 100                                         (defect; 85-100 is a
                                                                 non-fatal warning)
  * line 1 is a level-1 heading, line 2 is non-heading prose   (defect)
  * every "## " heading matches "## <n>. <Title>"              (defect)
  * no "### " heading outside section 6 (Absolute Rules)       (defect)
  * a bold "**tagline**" as the first non-blank line of every
    section                                                    (defect)
  * a "The test: ... ." line in every section except 2
    (Boundaries) and 6 (Absolute Rules)                        (defect)
  * no bare MUST/NEVER/ALWAYS outside section 6                (defect)
  * at most one fenced code block                              (defect)
  * no " you "/" we "/" I " in prose                            (defect)
  * last non-blank line starts with "Working if:"              (defect)
  * no bare http(s):// URL outside an HTML comment              (defect)
  * a provenance HTML comment in the first 10 lines            (defect)
  * every "@docs/agents/..." reference resolves to a file on
    disk, relative to --repo                                   (defect)

Usage:
    python lint_agents_kernel.py --file AGENTS.md --repo .
    python lint_agents_kernel.py --file AGENTS.md --repo . --json

Exit code 0 if no defects, 1 if any defect, 2 on a usage/IO error. Standard library only.
"""

from __future__ import annotations

import argparse
import json
import sys
import re
from pathlib import Path

HEADING_RE = re.compile(r"^(#{1,6})\s+(.*\S)\s*$")
H2_NUMBERED_RE = re.compile(r"^## (\d+)\. [A-Z]")
TAGLINE_RE = re.compile(r"^\*\*.+\*\*$")
TEST_LINE_RE = re.compile(r"^The test: .+\.$")
BARE_MODAL_RE = re.compile(r"(?<![\w-])(MUST|NEVER|ALWAYS)(?![\w-])")
FENCE_RE = re.compile(r"^```")
BARE_URL_RE = re.compile(r"https?://")
AT_REF_RE = re.compile(r"@([\w./-]+\.md)")
WEAK_PRONOUN_RE = re.compile(r" (you|we|I) ")

EXEMPT_SECTIONS = ("2", "6")  # Boundaries, Absolute Rules — no "The test:" line required


def lint_agents_kernel(path: Path, repo: Path) -> dict:
    text = path.read_text(encoding="utf-8", errors="ignore")
    lines = text.split("\n")

    n = len(lines)
    while n > 0 and not lines[n - 1].strip():
        n -= 1  # trailing blank lines don't count toward the cap

    defects: list[dict] = []
    warnings: list[dict] = []

    if n > 100:
        defects.append({"kind": "line-cap", "line": n, "detail": f"{n} lines, cap is 100"})
    elif n >= 85:
        warnings.append({"kind": "line-cap-warning", "line": n,
                          "detail": f"{n} lines, approaching the 100-line cap"})

    if not lines or not lines[0].startswith("# "):
        defects.append({"kind": "opening-shape", "line": 1,
                         "detail": "line 1 must be a level-1 heading"})

    heads = [(i, m) for i, m in ((j, HEADING_RE.match(l)) for j, l in enumerate(lines)) if m]

    first_h2_line = next((i for i, m in heads if m.group(1) == "##"), n)
    preamble = lines[1:first_h2_line]
    if not any(l.strip() and not HEADING_RE.match(l) for l in preamble):
        defects.append({"kind": "opening-shape", "line": 2,
                         "detail": "no description prose between the title and the first section"})
    h2s = [(i, m) for i, m in heads if m.group(1) == "##"]

    # locate section 6 (Absolute Rules)'s line range so its exemptions apply only inside it
    section6_range = (n, n)
    for idx, (i, _m) in enumerate(h2s):
        numbered = H2_NUMBERED_RE.match(lines[i])
        if numbered and numbered.group(1) == "6":
            end = h2s[idx + 1][0] if idx + 1 < len(h2s) else n
            section6_range = (i, end)

    def in_section6(i: int) -> bool:
        return section6_range[0] <= i < section6_range[1]

    for i, l in enumerate(lines):
        if l.startswith("## ") and not H2_NUMBERED_RE.match(l):
            defects.append({"kind": "heading-shape", "line": i + 1, "detail": l.strip()})
        if l.startswith("### ") and not in_section6(i):
            defects.append({"kind": "stray-h3", "line": i + 1, "detail": l.strip()})
        if BARE_MODAL_RE.search(l) and not in_section6(i) and not l.lstrip().startswith("#"):
            defects.append({"kind": "bare-modal-outside-rules", "line": i + 1, "detail": l.strip()})
        if WEAK_PRONOUN_RE.search(l):
            defects.append({"kind": "weak-pronoun", "line": i + 1, "detail": l.strip()})
        if BARE_URL_RE.search(l) and "<!--" not in l:
            defects.append({"kind": "bare-url", "line": i + 1, "detail": l.strip()})

    for idx, (i, _m) in enumerate(h2s):
        numbered = H2_NUMBERED_RE.match(lines[i])
        sec_no = numbered.group(1) if numbered else None
        end = h2s[idx + 1][0] if idx + 1 < len(h2s) else n
        body = lines[i + 1:end]
        first_nonblank = next((l for l in body if l.strip()), "")
        if not TAGLINE_RE.match(first_nonblank.strip()):
            defects.append({"kind": "missing-tagline", "line": i + 1, "detail": lines[i].strip()})
        if sec_no not in EXEMPT_SECTIONS:
            if not any(TEST_LINE_RE.match(l.strip()) for l in body):
                defects.append({"kind": "missing-test-line", "line": i + 1, "detail": lines[i].strip()})

    fence_count = sum(1 for l in lines if FENCE_RE.match(l.strip())) // 2
    if fence_count > 1:
        defects.append({"kind": "too-many-code-blocks", "line": 0,
                         "detail": f"{fence_count} fenced blocks, max 1"})

    if not any("<!--" in l for l in lines[:10]):
        defects.append({"kind": "missing-provenance", "line": 0,
                         "detail": "no HTML-comment provenance in first 10 lines"})

    stripped = [l for l in lines[:n] if l.strip()]
    if not stripped or not stripped[-1].startswith("Working if:"):
        defects.append({"kind": "missing-working-if", "line": n,
                         "detail": "last line must start with 'Working if:'"})

    for i, l in enumerate(lines):
        for m in AT_REF_RE.finditer(l):
            target = m.group(1)
            if not (repo / target).resolve().exists():
                defects.append({"kind": "dangling-at-ref", "line": i + 1, "detail": f"@{target}"})

    return {"file": str(path), "defects": defects, "warnings": warnings}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--file", required=True, type=Path, help="the AGENTS.md-shaped file to check")
    ap.add_argument("--repo", type=Path, default=Path("."),
                     help="repo root, for resolving @docs/agents/... references (default: .)")
    ap.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = ap.parse_args()

    if not args.file.is_file():
        print(f"error: not a file: {args.file}", file=sys.stderr)
        return 2

    result = lint_agents_kernel(args.file, args.repo)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        if not result["defects"]:
            print(f"CLEAN    {result['file']}")
        for d in result["defects"]:
            loc = f":{d['line']}" if d["line"] else ""
            print(f"DEFECT   {result['file']}{loc}  {d['kind']}: {d['detail']}")
        for w in result["warnings"]:
            loc = f":{w['line']}" if w["line"] else ""
            print(f"WARNING  {result['file']}{loc}  {w['kind']}: {w['detail']}")

    return 1 if result["defects"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
