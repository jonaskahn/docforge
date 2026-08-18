"""Portable, bounded illustration metrics for Docforge Markdown."""

from __future__ import annotations

import re

FENCE = re.compile(r"^\s*(`{3,})([\w-]*)")
CONNECTOR = re.compile(r"(?:-->|--|\|\|--|->>|-->>)")

# Maximum meaningful elements within a single illustration, per target depth.
# There is deliberately no cap on the number of illustrations in a document:
# every documentation authority surveyed prescribes splitting a dense diagram
# into several simpler ones, so a count cap would forbid the recommended remedy.
BUDGETS = {
    "orientation": 5,
    # Documented in illustration.md's budget table and previously unenforced:
    # the missing key silently resolved to the deep-dive bound of 12. A view may
    # declare `depth: working` to be sized at this bound inside a document of a
    # different depth.
    "working": 8,
    "deep-dive": 12,
    "reference": 12,
    "router": 12,
}
# Below this a diagram carries no relationship a sentence could not carry.
# Adding one is decoration, and decoration is not neutral: the seductive-detail
# effect is small, negative, and reproduced across dozens of studies, while the
# coherence principle (exclude extraneous pictures) is among the best-supported
# findings in multimedia learning.
MIN_MEANINGFUL_ELEMENTS = 3
# Accessibility directives and a closing `}` are not diagram elements.
MERMAID_DIRECTIVE = re.compile(r"^(?:accTitle|accDescr)\s*:|^\}$")


def is_explanatory_prose(line: str) -> bool:
    """A sentence a reader could use instead of seeing the picture."""
    stripped = line.strip()
    if not stripped or stripped.startswith(("#", "|", ">", "```", "~~~", "<!--", "_Last reviewed")):
        return False
    words = re.findall(r"[A-Za-z]{2,}", stripped)
    return len(words) >= 6


def has_adjacent_prose(lines: list[str], start: int, end: int, window: int = 4) -> bool:
    """Prose within `window` lines above the opening or below the closing fence.

    Adjacency is the point, not mere presence somewhere in the document: a
    reader whose renderer or screen reader drops the diagram must find the same
    relationships right there, and splitting the explanation away from the
    picture splits the reader's attention."""
    before = lines[max(0, start - 1 - window):max(0, start - 1)]
    after = lines[end:end + window]
    return any(is_explanatory_prose(line) for line in [*before, *after])


def illustration_defects(text: str, target_depth: str) -> list[dict]:
    defects: list[dict] = []
    lines = text.splitlines()
    blocks: list[tuple[str, int, list[str], int]] = []
    active: tuple[str, int, list[str], str] | None = None
    for number, line in enumerate(lines, 1):
        match = FENCE.match(line)
        if match:
            marker, language = match.group(1), match.group(2)
            if active is None:
                active = (language, number, [], marker)
            elif marker == active[3]:
                blocks.append((active[0], active[1], active[2], number))
                active = None
            continue
        if active is not None:
            active[2].append(line)
    if active is not None:
        defects.append({"kind": "unclosed illustration fence", "line": active[1], "detail": active[0] or "untagged"})
    max_elements = BUDGETS.get(target_depth, BUDGETS["deep-dive"])
    for language, line, rows, end in blocks:
        structural_ascii = language in {"text", "ascii"} and any(CONNECTOR.search(row) for row in rows)
        if language not in {"mermaid", "text", "ascii"} or (language in {"text", "ascii"} and not structural_ascii):
            continue
        # `accTitle:` / `accDescr:` are accessibility directives, not elements:
        # they must not be counted toward a budget and must not be mistaken for
        # the diagram declaration.
        content = [
            row.strip() for row in rows
            if row.strip()
            and not row.strip().startswith("%%")
            and not MERMAID_DIRECTIVE.match(row.strip())
        ]
        if language == "mermaid":
            kind = content[0].split()[0] if content else ""
            if kind == "stateDiagram":
                defects.append({"kind": "deprecated state diagram", "line": line, "detail": "use stateDiagram-v2"})
            if any(re.search(r"(?:^|\s)(?:style|classDef|click)\b", row) for row in content):
                defects.append({"kind": "invalid mermaid", "line": line, "detail": "forbidden directive"})
            if kind == "sequenceDiagram":
                participants = sum(1 for row in content if row.startswith("participant "))
                messages = sum(1 for row in content if re.search(r"(?:->>|-->>)", row))
                if participants > 5 or messages > 12:
                    defects.append({"kind": "illustration budget", "line": line, "detail": "sequence exceeds 5 participants or 12 messages"})
            if kind == "journey":
                sections = sum(1 for row in content if row.startswith("section "))
                if sections > 4:
                    defects.append({"kind": "illustration budget", "line": line, "detail": "journey exceeds 4 sections"})
            if kind in {"journey", "timeline"}:
                elements = sum(
                    1 for row in content[1:]
                    if row and row != "title" and not row.startswith(("title ", "section "))
                )
            else:
                elements = sum(1 for row in content[1:] if CONNECTOR.search(row) or row.startswith(("participant ", "state ", "    ")))
        else:
            elements = sum(1 for row in content if not CONNECTOR.search(row))
        if elements > max_elements:
            defects.append({"kind": "illustration budget", "line": line, "detail": f"{elements} elements exceeds {max_elements}"})
        if language == "mermaid" and elements and elements < MIN_MEANINGFUL_ELEMENTS:
            defects.append({
                "kind": "decorative illustration",
                "line": line,
                "detail": f"{elements} meaningful elements; state this in a sentence instead",
            })
        if not has_adjacent_prose(lines, line, end):
            defects.append({
                "kind": "undescribed illustration",
                "line": line,
                "detail": "no explanatory sentence beside the fence",
            })
        if language == "mermaid" and any(
            re.search(r"(?:^|[\s\[(>|-])end(?:[\s\]\)<|-]|$)", row) for row in content
        ):
            defects.append({
                "kind": "invalid mermaid",
                "line": line,
                "detail": "lowercase `end` breaks rendering; capitalize or wrap it",
            })
    return defects
