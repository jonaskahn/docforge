#!/usr/bin/env python3
"""
lint_document.py — mechanical pre-audit of ONE docforge document.

Runs the purely mechanical checks so the independent audit
(references/document-audit.md) spends its judgement on depth, grounding and
mode rather than on things a regex catches. It never replaces the agent: a
clean mechanical pass is necessary, not sufficient.

Checks, for the single file given:
  * unfilled `{{…}}` scaffold markers               (defect)
  * empty headings (a heading with no body before   (defect)
    the next heading or EOF)
  * dead relative links (a `](path)` or `](path.md#anchor)`
    whose target file does not exist on disk)        (defect)
  * unlinked file mentions (a backtick-quoted path    (defect)
    like `` `docs/x.md` `` naming a real file on disk,
    written as plain text instead of a markdown link)
  * missing must-present headings passed via         (defect)
    --require-heading (repeatable, substring match)
Typed `<UPPER_SNAKE>` tokens are reported separately and are NOT defects —
they are the intentional stand-ins for genuinely external values.

Usage:
    python lint_document.py --file docs/architecture/high-level.md
    python lint_document.py --file docs/flows/checkout.md \\
        --require-heading "## " --require-heading "Steps"
    python lint_document.py --file docs/x.md --json

Exit code 0 if no defects, 1 if any defect, 2 on a usage/IO error — so it can
gate a step. Standard library only.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from provenance_frontmatter import (
    BLOB,
    FLOW_VALUES,
    PROVENANCE_FIELDS,
    SCAFFOLD_TOKEN,
    SOURCE_ROLES,
    parse_frontmatter as codec_parse_frontmatter,
)

SCAFFOLD_RE = re.compile(r"\{\{.*?\}\}")
TOKEN_RE = re.compile(r"<[A-Z][A-Z0-9_]*>")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*\S)\s*$")
# Markdown links whose target is not a URL, mailto, or pure in-page anchor.
LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
# A backtick-quoted path ending in .md — a candidate cross-reference that
# should be an actual link, not bare text naming the file.
MENTION_RE = re.compile(r"`([A-Za-z0-9_./-]+\.md)`")
FORGE_RE = re.compile(
    r"\b(github|gitlab|bitbucket|gitea|forgejo|sourcehut|azure devops|"
    r"github actions|gitlab ci|codeowners)\b",
    re.IGNORECASE,
)
FENCE_RE = re.compile(r"^(`{3,})(\w*)")
MERMAID_FORBIDDEN_RE = re.compile(r"(?:^|\s)(style\s|classDef|click\s)")
MERMAID_RESERVED_NODE_RE = re.compile(r"\b(end|graph|subgraph)\b\s*[\[\(\{]", re.IGNORECASE)
TREE_GLYPH_RE = re.compile(r"[│├└┌]")
SCALAR_PROVENANCE_FIELDS = PROVENANCE_FIELDS - {"graph", "sections", "generator"}
MARKDOWN_EXCEPTIONS = {"AGENTS.md", "CLAUDE.md", "CLAUDE.local.md"}


def is_external_link(target: str) -> bool:
    t = target.strip()
    return (
        t.startswith("http://")
        or t.startswith("https://")
        or t.startswith("mailto:")
        or t.startswith("#")
        or t.startswith("<")  # a token used as a placeholder URL
    )


def heading_anchor(value: str) -> str:
    value = re.sub(r"[^\w\s-]", "", value.strip().lower(), flags=re.UNICODE)
    return re.sub(r"[\s-]+", "-", value).strip("-")


def repository_root(path: Path) -> Path:
    for parent in [path.parent, *path.parents]:
        if (parent / ".git").exists() or (parent / ".docforge").exists():
            return parent
    return path.parent


def illustration_defects(text: str) -> list[dict]:
    defects: list[dict] = []
    in_fence = False
    fence_marker = ""
    fence_lang = ""
    for i, line in enumerate(text.splitlines(), 1):
        stripped = line.strip()
        fence_match = FENCE_RE.match(stripped)
        if fence_match:
            marker = fence_match.group(1)
            lang = fence_match.group(2)
            if not in_fence:
                in_fence = True
                fence_marker = marker
                fence_lang = lang
            elif marker == fence_marker:
                in_fence = False
                fence_marker = ""
                fence_lang = ""
            continue
        if not in_fence:
            continue
        if fence_lang == "mermaid":
            if MERMAID_FORBIDDEN_RE.search(line) or MERMAID_RESERVED_NODE_RE.search(line):
                defects.append({
                    "kind": "invalid mermaid", "line": i,
                    "detail": "forbidden directive or reserved node id",
                })
        elif fence_lang not in {"text", "ascii"} and TREE_GLYPH_RE.search(line):
            defects.append({
                "kind": "untagged ascii fence", "line": i,
                "detail": "tree glyphs in non-text fence",
            })
    return defects


def provenance_defects(path: Path, text: str) -> list[dict]:
    defects: list[dict] = []
    if path.name in MARKDOWN_EXCEPTIONS:
        return defects
    state, provenance, body_start = codec_parse_frontmatter(text)
    if state == "missing":
        return [{"kind": "missing provenance", "line": 1, "detail": "frontmatter absent"}]
    if state == "unparseable":
        return [{"kind": "unparseable provenance", "line": 1, "detail": "frontmatter unparseable"}]
    if state == "obsolete":
        return [{"kind": "obsolete schema", "line": 1, "detail": "run migrate_metadata.py"}]
    if state == "legacy":
        return [{"kind": "legacy provenance", "line": 1, "detail": "schema absent"}]
    if not isinstance(provenance, dict):
        return [{"kind": "missing provenance", "line": 1, "detail": "docforge_provenance absent"}]
    missing = sorted(PROVENANCE_FIELDS - set(provenance))
    graph = provenance.get("graph")
    if not isinstance(graph, dict) or not {"provider", "flow"} <= set(graph):
        missing.append("graph.provider/flow")
    generator = provenance.get("generator")
    if not isinstance(generator, dict) or not {"name", "version"} <= set(generator):
        missing.append("generator.name/version")
    invalid = [
        key for key in SCALAR_PROVENANCE_FIELDS
        if not isinstance(provenance.get(key), str)
        or not provenance[key]
        or SCAFFOLD_TOKEN.fullmatch(provenance[key])
    ]
    if isinstance(generator, dict):
        for key in ("name", "version"):
            value = generator.get(key)
            if not isinstance(value, str) or not value or SCAFFOLD_TOKEN.fullmatch(value):
                invalid.append(f"generator.{key}")
    elif "generator" not in invalid:
        invalid.append("generator")
    if isinstance(graph, dict):
        invalid.extend(
            f"graph.{key}" for key in ("provider", "flow")
            if not isinstance(graph.get(key), str)
            or not graph[key]
            or SCAFFOLD_TOKEN.fullmatch(graph[key])
        )
    if missing or invalid or provenance.get("schema") != "2.0" or "graph_snapshot" in provenance:
        detail = ", ".join(missing + [f"non-concrete {item}" for item in invalid])
        defects.append({
            "kind": "missing provenance", "line": 1,
            "detail": detail or "invalid schema or obsolete graph_snapshot",
        })
    if isinstance(graph, dict) and graph.get("flow") not in FLOW_VALUES:
        defects.append({"kind": "missing provenance", "line": 1, "detail": "invalid graph.flow"})
    git_commit = provenance.get("git_commit")
    if git_commit is not None and (
        not isinstance(git_commit, str) or not BLOB.fullmatch(git_commit)
    ):
        defects.append({"kind": "missing provenance", "line": 1, "detail": "invalid git_commit"})
    sections = provenance.get("sections")
    if not isinstance(sections, list):
        defects.append({"kind": "missing provenance", "line": 1, "detail": "sections must be an array"})
        return defects
    if not sections:
        defects.append({"kind": "empty provenance", "line": 1, "detail": "sections is empty"})
    body = text[body_start:]
    anchors = {
        heading_anchor(heading.group(2))
        for line in body.splitlines()
        if (heading := HEADING_RE.match(line))
    }
    root = repository_root(path)
    for section in sections:
        section_id = section.get("id") if isinstance(section, dict) else None
        if not isinstance(section_id, str) or section_id not in anchors:
            defects.append({
                "kind": "unknown section", "line": 1,
                "detail": section_id if isinstance(section_id, str) else "<missing>",
            })
        if not isinstance(section, dict) or not isinstance(section.get("sources"), list) or not isinstance(section.get("unresolved"), list):
            defects.append({"kind": "missing provenance", "line": 1, "detail": f"section {section_id or '<missing>'} shape"})
            continue
        for source in section["sources"]:
            source_path = source.get("path", "") if isinstance(source, dict) else ""
            blob = source.get("git_blob") if isinstance(source, dict) else None
            role = source.get("role") if isinstance(source, dict) else None
            if not isinstance(blob, str) or not BLOB.fullmatch(blob):
                defects.append({"kind": "invalid blob", "line": 1, "detail": source_path or "<missing>"})
            if not source_path or not (root / source_path).is_file():
                defects.append({"kind": "unknown source", "line": 1, "detail": source_path or "<missing>"})
            if role not in SOURCE_ROLES:
                defects.append({"kind": "missing provenance", "line": 1, "detail": f"{source_path or '<missing>'}: invalid role"})
    return defects


def lint_document(path: Path, require_headings: list[str]) -> dict:
    text = path.read_text(encoding="utf-8", errors="ignore")
    lines = text.split("\n")
    defects: list[dict] = []
    tokens: list[str] = []
    defects.extend(provenance_defects(path, text))
    defects.extend(illustration_defects(text))

    # scaffold markers + tokens, with line numbers
    for i, line in enumerate(lines, 1):
        for m in SCAFFOLD_RE.finditer(line):
            defects.append({"kind": "scaffold-marker", "line": i, "detail": m.group(0)})
        for m in TOKEN_RE.finditer(line):
            tokens.append(m.group(0))

    # empty headings: a heading immediately followed by another heading or EOF,
    # with nothing but blank lines between.
    heading_lines = [(i, HEADING_RE.match(l)) for i, l in enumerate(lines)]
    heads = [(i, m) for i, m in heading_lines if m]
    headings_text = [m.group(2) for _, m in heads]
    for idx, (i, m) in enumerate(heads):
        # find the next non-blank line after this heading
        body_found = False
        j = i + 1
        next_head_line = heads[idx + 1][0] if idx + 1 < len(heads) else len(lines)
        while j < next_head_line:
            if lines[j].strip():
                body_found = True
                break
            j += 1
        if not body_found:
            defects.append({"kind": "empty-heading", "line": i + 1, "detail": m.group(2)})

    # dead relative links
    repo_dir = path.parent
    linked_targets: set[str] = set()
    for i, line in enumerate(lines, 1):
        for m in LINK_RE.finditer(line):
            target = m.group(1).strip()
            linked_targets.add(target.split("#", 1)[0])
            if is_external_link(target):
                continue
            file_part = target.split("#", 1)[0]
            if not file_part:  # pure anchor already handled by is_external_link
                continue
            resolved = (repo_dir / file_part).resolve()
            if not resolved.exists():
                defects.append({"kind": "dead-link", "line": i, "detail": target})

    # unlinked file mentions: a real file named in backticks, never linked
    for i, line in enumerate(lines, 1):
        for m in MENTION_RE.finditer(line):
            target = m.group(1)
            if target in linked_targets or target.split("/")[-1] in linked_targets:
                continue  # this doc already links to it elsewhere
            before = line[m.start() - 1] if m.start() > 0 else ""
            after = line[m.end():m.end() + 2]
            if before == "[" and after.startswith("("):
                continue  # `` `file.md` `` used as the label of its own link
            resolved = (repo_dir / target).resolve()
            if resolved.exists():
                defects.append({"kind": "unlinked-mention", "line": i, "detail": target})

    # required headings (substring match against any heading in the doc)
    for req in require_headings:
        if not any(req in h for h in headings_text):
            defects.append({"kind": "missing-heading", "line": 0, "detail": req})

    for i, line in enumerate(lines, 1):
        for match in FORGE_RE.finditer(line):
            defects.append({"kind": "forge-leakage", "line": i, "detail": match.group(0)})

    return {"file": str(path), "defects": defects, "tokens": sorted(set(tokens))}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--file", required=True, type=Path, help="the single document to check")
    ap.add_argument("--require-heading", action="append", default=[], dest="require_heading",
                    help="a heading substring that must appear (repeatable)")
    ap.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = ap.parse_args()

    if not args.file.is_file():
        print(f"error: not a file: {args.file}", file=sys.stderr)
        return 2

    result = lint_document(args.file, args.require_heading)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        if not result["defects"]:
            print(f"CLEAN    {result['file']}")
        for d in result["defects"]:
            loc = f":{d['line']}" if d["line"] else ""
            print(f"DEFECT   {result['file']}{loc}  {d['kind']}: {d['detail']}")
        if result["tokens"]:
            print(f"tokens (external, not defects): {', '.join(result['tokens'])}")

    return 1 if result["defects"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
