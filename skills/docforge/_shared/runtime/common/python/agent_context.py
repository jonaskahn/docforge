"""Manifest-scoped isolation checks for generated agent-context output.

Human-facing output must not reference an active agent-context output. Agent-
context output is stricter: it must not contain Markdown links, raw URLs,
document imports, or bare references to managed documents and agent outputs.
Both checks inspect the complete generated file, including comments and fenced
examples. Internal Docforge documentation is never scanned here.
"""

from __future__ import annotations

import re
from pathlib import PurePosixPath

AGENT_CONTEXT_GROUP = "agent-context"
INACTIVE_STATUSES = {"skipped", "retired"}
MARKDOWN_LINK_RE = re.compile(r"!?\[([^\]\n]*)\]\(([^)\n]*)\)")
RAW_URL_RE = re.compile(r"\bhttps?://[^\s<>)\]\"']+")
AT_IMPORT_RE = re.compile(
    r"(?<![\w@])@((?:(?:\.{1,2}/|/)?[\w.~+-]+)(?:/[\w.~+-]+)*/?(?:#[\w.~:-]+)?)"
)
PATH_TOKEN_RE = re.compile(
    r"(?<![\w@])((?:(?:\.{1,2}/|/)?(?:[\w.~+-]+/)*[\w.~+-]+\."
    r"(?:md|mdx|markdown|rst|adoc|asciidoc)(?:#[\w.~:-]+)?|docs/[\w.~+/-]*))"
    r"(?![\w./-])",
    re.IGNORECASE,
)
PATH_CHAR_RE = re.compile(r"[\w./-]")
AGENT_DIRECTORY_PREFIX = "docs/agents/"


def _active_documents(manifest: dict) -> list[dict]:
    return [
        doc
        for doc in manifest.get("documents", [])
        if doc.get("status") not in INACTIVE_STATUSES
    ]


def agent_context_targets(manifest: dict) -> tuple[set[str], set[str]]:
    """Return active agent output paths and selected agent-directory prefixes."""
    paths = {
        doc["path"]
        for doc in _active_documents(manifest)
        if doc.get("group") == AGENT_CONTEXT_GROUP
        and isinstance(doc.get("path"), str)
    }
    prefixes = (
        {AGENT_DIRECTORY_PREFIX}
        if any(path.startswith(AGENT_DIRECTORY_PREFIX) for path in paths)
        else set()
    )
    return paths, prefixes


def _managed_document_paths(manifest: dict) -> set[str]:
    """Manifest outputs that are documents rather than machine configuration."""
    return {
        doc["path"]
        for doc in _active_documents(manifest)
        if doc.get("type") != "machine-config"
        and isinstance(doc.get("path"), str)
    }


def _matches(target: str, paths: set[str], prefixes: set[str]) -> bool:
    if target in paths:
        return True
    return any(
        target == prefix.rstrip("/") or target.startswith(prefix)
        for prefix in prefixes
    )


def _collapse(path: str) -> str:
    """Resolve ``..`` segments without touching the filesystem."""
    parts: list[str] = []
    for part in path.split("/"):
        if part in ("", "."):
            continue
        if part == "..":
            if parts:
                parts.pop()
            continue
        parts.append(part)
    return "/".join(parts)


def _clean_reference(raw: str) -> str:
    value = raw.strip().strip("`\"'<>")
    return value.rstrip(".,;:!?")


def _reference_candidates(raw: str, base: PurePosixPath) -> list[str]:
    value = _clean_reference(raw)
    if not value or value.startswith(("http://", "https://", "mailto:")):
        return []
    value = value.split("#", 1)[0].split("?", 1)[0]
    if not value:
        return []

    direct = _collapse(value.lstrip("/"))
    relative = _collapse(f"{base.as_posix()}/{value}")
    if value.startswith("/"):
        candidates = [direct]
    elif value.startswith(("./", "../")):
        candidates = [relative, direct]
    elif value.startswith(("docs/", ".claude/")):
        candidates = [direct, relative]
    else:
        candidates = [relative, direct]
    return list(dict.fromkeys(candidate for candidate in candidates if candidate))


def _matched_reference(
    raw: str,
    base: PurePosixPath,
    paths: set[str],
    prefixes: set[str],
) -> str | None:
    return next(
        (
            candidate
            for candidate in _reference_candidates(raw, base)
            if _matches(candidate, paths, prefixes)
        ),
        None,
    )


def _link_target(raw: str) -> str:
    value = raw.strip()
    if value.startswith("<") and ">" in value:
        return value[1:value.index(">")]
    return value.split(maxsplit=1)[0] if value else ""


def _looks_like_path_import(raw: str) -> bool:
    value = _clean_reference(raw).split("#", 1)[0].split("?", 1)[0]
    value = value.rstrip("/")
    if value.startswith(("docs/", ".claude/", "./", "../", "/")):
        return True
    return bool(PurePosixPath(value).suffix)


def _mask_spans(line: str, spans: list[tuple[int, int]]) -> str:
    if not spans:
        return line
    chars = list(line)
    for start, end in spans:
        chars[start:end] = " " * (end - start)
    return "".join(chars)


def _overlaps(start: int, end: int, spans: list[tuple[int, int]]) -> bool:
    return any(start < claimed_end and claimed_start < end for claimed_start, claimed_end in spans)


def _bare_references(
    line: str,
    base: PurePosixPath,
    paths: set[str],
    prefixes: set[str],
) -> list[str]:
    """Return managed paths mentioned outside links, URLs, and imports."""
    found: list[str] = []
    claimed: list[tuple[int, int]] = []

    for match in PATH_TOKEN_RE.finditer(line):
        target = _matched_reference(match.group(1), base, paths, prefixes)
        if target:
            found.append(target)
            claimed.append(match.span(1))

    for literal, is_prefix in [
        *((path, False) for path in sorted(paths, key=lambda item: (-len(item), item))),
        *((prefix, True) for prefix in sorted(prefixes, key=lambda item: (-len(item), item))),
    ]:
        cursor = 0
        while (start := line.find(literal, cursor)) != -1:
            end = start + len(literal)
            cursor = end
            if start and PATH_CHAR_RE.match(line[start - 1]):
                continue
            if not is_prefix and end < len(line) and PATH_CHAR_RE.match(line[end]):
                continue
            reference_end = end
            if is_prefix:
                while reference_end < len(line) and PATH_CHAR_RE.match(line[reference_end]):
                    reference_end += 1
            if _overlaps(start, reference_end, claimed):
                continue
            raw = line[start:reference_end]
            target = _matched_reference(raw, base, paths, prefixes)
            if target:
                found.append(target)
                claimed.append((start, reference_end))
    return found


def _record(
    findings: list[dict],
    seen: set[tuple[int, str, str]],
    line: int,
    target: str,
    kind: str,
) -> None:
    key = (line, target, kind)
    if key not in seen:
        seen.add(key)
        findings.append({"line": line, "target": target, "kind": kind})


def agent_context_leaks(doc: dict, manifest: dict, text: str) -> list[dict]:
    """Return non-agent references to active agent outputs.

    The API remains compatible with the former ``{line, target}`` records and
    adds ``kind`` so audit output can identify links, imports, and bare paths.
    """
    if doc.get("group") == AGENT_CONTEXT_GROUP:
        return []
    paths, prefixes = agent_context_targets(manifest)
    if not paths:
        return []

    base = PurePosixPath(doc["path"]).parent
    findings: list[dict] = []
    seen: set[tuple[int, str, str]] = set()
    for number, line in enumerate(text.splitlines(), 1):
        destination_spans: list[tuple[int, int]] = []
        for match in MARKDOWN_LINK_RE.finditer(line):
            target = _link_target(match.group(2))
            matched = _matched_reference(target, base, paths, prefixes)
            if matched:
                _record(findings, seen, number, matched, "markdown-link")
            destination_spans.append(match.span(2))

        working = _mask_spans(line, destination_spans)
        url_spans = [match.span() for match in RAW_URL_RE.finditer(working)]
        working = _mask_spans(working, url_spans)

        import_spans: list[tuple[int, int]] = []
        for match in AT_IMPORT_RE.finditer(working):
            matched = _matched_reference(match.group(1), base, paths, prefixes)
            if matched:
                _record(findings, seen, number, matched, "at-import")
            import_spans.append(match.span())
        working = _mask_spans(working, import_spans)

        for target in _bare_references(working, base, paths, prefixes):
            _record(findings, seen, number, target, "agent-output-path")
    return findings


def agent_context_outbound_findings(doc: dict, manifest: dict, text: str) -> list[dict]:
    """Return forbidden references emitted by an agent-context output."""
    if doc.get("group") != AGENT_CONTEXT_GROUP:
        return []

    agent_paths, prefixes = agent_context_targets(manifest)
    managed_paths = _managed_document_paths(manifest)
    reference_paths = agent_paths | managed_paths
    base = PurePosixPath(doc["path"]).parent
    findings: list[dict] = []
    seen: set[tuple[int, str, str]] = set()

    for number, line in enumerate(text.splitlines(), 1):
        link_spans: list[tuple[int, int]] = []
        for match in MARKDOWN_LINK_RE.finditer(line):
            target = _link_target(match.group(2)) or "<empty>"
            _record(findings, seen, number, target, "markdown-link")
            link_spans.append(match.span())
        working = _mask_spans(line, link_spans)

        url_spans: list[tuple[int, int]] = []
        for match in RAW_URL_RE.finditer(working):
            _record(findings, seen, number, match.group(0), "raw-url")
            url_spans.append(match.span())
        working = _mask_spans(working, url_spans)

        import_spans: list[tuple[int, int]] = []
        for match in AT_IMPORT_RE.finditer(working):
            raw = match.group(1)
            matched = _matched_reference(raw, base, reference_paths, prefixes)
            if matched or _looks_like_path_import(raw):
                _record(findings, seen, number, matched or _clean_reference(raw), "at-import")
                import_spans.append(match.span())
        working = _mask_spans(working, import_spans)

        for target in _bare_references(working, base, reference_paths, prefixes):
            kind = (
                "agent-output-path"
                if _matches(target, agent_paths, prefixes)
                else "managed-document-path"
            )
            _record(findings, seen, number, target, kind)
    return findings
