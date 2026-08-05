"""Portable, bounded illustration metrics for Docforge Markdown."""

from __future__ import annotations

import re

FENCE = re.compile(r"^\s*(`{3,})([\w-]*)")
CONNECTOR = re.compile(r"(?:-->|--|\|\|--|->>|-->>)")

BUDGETS = {
    "orientation": (1, 5),
    "deep-dive": (3, 12),
    "reference": (1, 12),
    "router": (0, 0),
}


def illustration_defects(text: str, target_depth: str) -> list[dict]:
    defects: list[dict] = []
    blocks: list[tuple[str, int, list[str]]] = []
    active: tuple[str, int, list[str], str] | None = None
    for number, line in enumerate(text.splitlines(), 1):
        match = FENCE.match(line)
        if match:
            marker, language = match.group(1), match.group(2)
            if active is None:
                active = (language, number, [], marker)
            elif marker == active[3]:
                blocks.append((active[0], active[1], active[2]))
                active = None
            continue
        if active is not None:
            active[2].append(line)
    if active is not None:
        defects.append({"kind": "unclosed illustration fence", "line": active[1], "detail": active[0] or "untagged"})
    illustrations = 0
    max_illustrations, max_elements = BUDGETS.get(target_depth, BUDGETS["deep-dive"])
    for language, line, rows in blocks:
        structural_ascii = language in {"text", "ascii"} and any(CONNECTOR.search(row) for row in rows)
        if language not in {"mermaid", "text", "ascii"} or (language in {"text", "ascii"} and not structural_ascii):
            continue
        illustrations += 1
        content = [row.strip() for row in rows if row.strip() and not row.strip().startswith("%%")]
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
    if illustrations > max_illustrations:
        defects.append({"kind": "illustration budget", "line": 1, "detail": f"{illustrations} illustrations exceeds {max_illustrations}"})
    return defects
