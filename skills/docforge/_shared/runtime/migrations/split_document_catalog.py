#!/usr/bin/env python3
"""One-shot: split references/document-catalog.md into references/catalog-contracts/.

Rows keyed by Type may list multiple aliased types (`docs-index / folder-index / ...`);
each listed type becomes its own contract file so lookups by type resolve.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent.parent
SOURCE = SKILL_ROOT / "references" / "document-catalog.md"
OUT_DIR = SKILL_ROOT / "references" / "catalog-contracts"

HEADER = """# Document catalog contracts

This directory owns content contracts: must-present material, keep-out
boundaries, primary mode, and target depth. Selection, paths, evidence
capabilities, write order, templates, and audit profiles are machine-readable
via `query_catalog` against `.metadata/catalog/`.

## Universal contract

Every substantive document must:

- answer the reader question implied by its type;
- cite the repository evidence used by each section;
- describe current behavior, boundaries, failure modes, and adjacent systems;
- keep rationale in decision records and volatile lookup facts in reference
  documents;
- link to facts owned elsewhere instead of repeating them;
- contain no unresolved scaffold markers.

Router/index documents orient and link. Procedure documents are executable in
order. Reference documents optimize lookup. Explanation documents establish
mechanism, constraints, and tradeoffs.

## Index

"""

ROW_RE = re.compile(
    r"^\|\s*(?P<types>[^|]+?)\s*\|\s*(?P<must>[^|]+?)\s*\|\s*(?P<keep>[^|]+?)\s*\|\s*"
    r"(?P<mode>[^|]+?)\s*\|\s*(?P<depth>[^|]+?)\s*\|\s*$"
)


def parse_rows(text: str) -> list[dict]:
    rows: list[dict] = []
    in_table = False
    for line in text.splitlines():
        if line.startswith("| Type | Must present |"):
            in_table = True
            continue
        if in_table and line.startswith("|---"):
            continue
        if in_table and not line.startswith("|"):
            break
        if not in_table:
            continue
        match = ROW_RE.match(line)
        if not match:
            continue
        types = [part.strip() for part in match.group("types").split("/") if part.strip()]
        rows.append(
            {
                "types": types,
                "must": match.group("must").strip(),
                "keep": match.group("keep").strip(),
                "mode": match.group("mode").strip(),
                "depth": match.group("depth").strip(),
            }
        )
    return rows


def trailing_sections(text: str) -> str:
    marker = "## Risk-register routing"
    idx = text.find(marker)
    if idx < 0:
        return ""
    return text[idx:].rstrip() + "\n"


def contract_body(type_id: str, row: dict, aliases: list[str]) -> str:
    alias_note = ""
    if aliases:
        alias_note = (
            f"\nAliased with: {', '.join(f'`{a}`' for a in aliases)} "
            "(same content contract).\n"
        )
    return (
        f"# `{type_id}`\n\n"
        f"Content contract for document type `{type_id}`.\n"
        f"{alias_note}\n"
        f"| Type | Must present | Keep out | Primary mode | Depth |\n"
        f"|---|---|---|---|---|\n"
        f"| {type_id} | {row['must']} | {row['keep']} | {row['mode']} | {row['depth']} |\n"
    )


def emit(*, dry_run: bool) -> int:
    if not SOURCE.is_file():
        print(f"error: missing {SOURCE}", file=sys.stderr)
        return 1
    text = SOURCE.read_text(encoding="utf-8")
    rows = parse_rows(text)
    if not rows:
        print("error: no contract table rows parsed", file=sys.stderr)
        return 1

    files: dict[str, str] = {}
    index_lines: list[str] = []
    for row in rows:
        types = row["types"]
        for type_id in types:
            aliases = [t for t in types if t != type_id]
            files[type_id] = contract_body(type_id, row, aliases)
            # Short must-present gist for README index
            gist = row["must"]
            if len(gist) > 90:
                gist = gist[:87].rstrip() + "…"
            index_lines.append(f"- `{type_id}` — {gist} → [{type_id}.md]({type_id}.md)")

    trailing = trailing_sections(text)
    readme = HEADER + "\n".join(index_lines) + "\n\n" + trailing

    if dry_run:
        print(f"would write {len(files)} contract files + README.md")
        for name in sorted(files):
            print(f"  {name}.md")
        return 0

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    # Clear prior contract files (keep directory).
    for path in OUT_DIR.glob("*.md"):
        path.unlink()
    (OUT_DIR / "README.md").write_text(readme, encoding="utf-8")
    for type_id, body in files.items():
        (OUT_DIR / f"{type_id}.md").write_text(body, encoding="utf-8")

    # Stub the monolith so leftover links still resolve.
    stub = (
        "# Document catalog\n\n"
        "This file has been split for context efficiency. Content contracts live in\n"
        "[`catalog-contracts/`](catalog-contracts/README.md). The machine catalog is\n"
        "queried via `runtime/cli/python/query_catalog.py` against `.metadata/catalog/`.\n\n"
        "Universal contract, risk-register routing, and typed profile behavior are\n"
        "preserved in [`catalog-contracts/README.md`](catalog-contracts/README.md).\n"
    )
    SOURCE.write_text(stub, encoding="utf-8")
    print(f"Wrote {len(files)} contracts under {OUT_DIR.relative_to(SKILL_ROOT)}/")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    return emit(dry_run=args.dry_run)


if __name__ == "__main__":
    raise SystemExit(main())
