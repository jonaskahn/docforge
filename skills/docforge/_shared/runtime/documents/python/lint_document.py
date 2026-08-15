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

from runtime.common.python.provenance_frontmatter import (
    BLOB,
    FLOW_VALUES,
    PROVENANCE_FIELDS,
    SCAFFOLD_TOKEN,
    SOURCE_ROLES,
    SUPPORTED_SCHEMA_VERSIONS,
    parse_frontmatter as codec_parse_frontmatter,
    parse_yaml_mapping,
    split_frontmatter,
)
from runtime.common.python import provenance_store as store
from runtime.common.python.evidence_locators import validate_locators
from runtime.common.python.special_files import SPECIAL_DOC_OUTPUTS
from runtime.common.python.illustration_metrics import illustration_defects as budget_defects
from runtime.common.python.markdown_fences import visible_presentation_defects

SCAFFOLD_RE = re.compile(r"\{\{.*?\}\}")
TOKEN_RE = re.compile(r"<[A-Z][A-Z0-9_]*>")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*\S)\s*$")
DESCRIPTION_LIMIT = 160
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
MARKDOWN_EXCEPTIONS = SPECIAL_DOC_OUTPUTS


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


def _metadata_context(path: Path, text: str) -> tuple[str, dict | None, int, dict]:
    """Resolve (state, provenance, body_start, public) for one document.

    In json storage mode the folder sidecar wins; inline frontmatter that
    has not been migrated yet reports state `inline` so lint flags it."""
    root = repository_root(path)
    storage = store.STORAGE_MARKDOWN
    manifest_path = root / ".docforge" / "manifest.json"
    if manifest_path.is_file():
        try:
            storage = store.storage_for(json.loads(manifest_path.read_text(encoding="utf-8")))
        except (ValueError, OSError):
            pass
    rel = path.relative_to(root).as_posix()
    if storage == store.STORAGE_JSON:
        entry = store.entry_for(root, rel)
        if isinstance(entry, dict) and isinstance(entry.get("provenance"), dict):
            public = {key: entry[key] for key in store.PUBLIC_FIELDS if entry.get(key)}
            return "ok", entry["provenance"], 0, public
        state, provenance, body_start = codec_parse_frontmatter(text)
        if state == "ok":
            state = "inline"
    else:
        state, provenance, body_start = codec_parse_frontmatter(text)
    public: dict = {}
    if state in {"ok", "inline"}:
        raw, _body, _end = split_frontmatter(text)
        if raw is not None:
            try:
                data = parse_yaml_mapping(raw)
            except Exception:  # noqa: BLE001 - provenance defects report parsing
                data = None
            if isinstance(data, dict):
                public = {key: data.get(key) for key in store.PUBLIC_FIELDS if data.get(key)}
    return state, provenance, body_start, public


def provenance_defects(path: Path, text: str) -> list[dict]:
    defects: list[dict] = []
    if path.name in MARKDOWN_EXCEPTIONS:
        return defects
    state, provenance, body_start, _public = _metadata_context(path, text)
    if state == "missing":
        return [{"kind": "missing provenance", "line": 1, "detail": "frontmatter absent"}]
    if state == "unparseable":
        return [{"kind": "unparseable provenance", "line": 1, "detail": "frontmatter unparseable"}]
    if state == "obsolete":
        return [{"kind": "obsolete schema", "line": 1, "detail": "run migrate_metadata.py"}]
    if state == "legacy":
        return [{"kind": "legacy provenance", "line": 1, "detail": "schema absent"}]
    if state == "inline":
        return [{"kind": "legacy provenance", "line": 1, "detail": "inline provenance in json mode; run migrate_metadata"}]
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
    if missing or invalid or provenance.get("schema") not in SUPPORTED_SCHEMA_VERSIONS or "graph_snapshot" in provenance:
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


def public_metadata_defects(path: Path, text: str) -> list[dict]:
    """Public metadata contract for written documents: a non-empty
    `description` of at most 160 characters."""
    if path.name in MARKDOWN_EXCEPTIONS:
        return []
    state, _provenance, _body_start, public = _metadata_context(path, text)
    if state not in {"ok", "inline"}:
        return []
    description = public.get("description")
    if not isinstance(description, str) or not description.strip():
        return [{"kind": "missing description", "line": 1, "detail": "public description is required"}]
    if len(description) > DESCRIPTION_LIMIT:
        return [{"kind": "long description", "line": 1, "detail": f"description exceeds {DESCRIPTION_LIMIT} characters"}]
    return []


def lint_document(path: Path, require_headings: list[str]) -> dict:
    text = path.read_text(encoding="utf-8", errors="ignore")
    lines = text.split("\n")
    defects: list[dict] = []
    tokens: list[str] = []
    defects.extend(provenance_defects(path, text))
    defects.extend(public_metadata_defects(path, text))
    defects.extend(illustration_defects(text))
    _state, provenance, _end, _public = _metadata_context(path, text)
    target_depth = provenance.get("target_depth", "deep-dive") if isinstance(provenance, dict) else "deep-dive"
    defects.extend(budget_defects(text, target_depth))
    defects.extend(validate_locators(path, text))
    defects.extend(visible_presentation_defects(text))

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
