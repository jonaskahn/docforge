"""The one-way agent-context reference boundary.

Agent-context documents may link any human-facing document. No human-facing
document may link, mention, or `@`-reference an agent-context output. The agent
overlay knows the whole tree; the tree reads as though the overlay does not
exist. See references/document-composition.md.

Targets are derived from the manifest, never hardcoded. A project that never
confirmed the `coding-agents` audience has an empty target set, so a repository
whose own source tree contains `agents/`, or which owns `.claude/settings.json`
independently, can never trip this check.
"""

from __future__ import annotations

import re
from pathlib import PurePosixPath

from runtime.common.python.markdown_fences import scan_fences

AGENT_CONTEXT_GROUP = "agent-context"
INACTIVE_STATUSES = {"skipped", "retired"}
LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
# Directories whose whole subtree belongs to the boundary. A target file
# directly under one of these contributes its parent as a prefix, so a link to
# a sibling the manifest does not list is still caught.
PREFIX_ROOTS = ("docs/agents/", ".claude/")


def agent_context_targets(manifest: dict) -> tuple[set[str], set[str]]:
    """Return (exact paths, directory prefixes) this project actually selected."""
    paths = {
        doc["path"]
        for doc in manifest.get("documents", [])
        if doc.get("group") == AGENT_CONTEXT_GROUP
        and doc.get("status") not in INACTIVE_STATUSES
    }
    prefixes = {
        PurePosixPath(path).parent.as_posix() + "/"
        for path in paths
        if path.startswith(PREFIX_ROOTS)
    }
    return paths, prefixes


def _matches(target: str, paths: set[str], prefixes: set[str]) -> bool:
    if target in paths:
        return True
    return any(target.startswith(prefix) for prefix in prefixes)


def _unfenced_lines(text: str) -> list[tuple[int, str]]:
    """Lines outside every fence.

    A fenced snippet quoting `AGENTS.md` -- a setup command, sample output -- is
    not a reference; excluding fences is what keeps this check honest."""
    protected: set[int] = set()
    for fence in scan_fences(text):
        end = fence.get("end") or len(text.splitlines())
        protected.update(range(fence["start"], end + 1))
    return [
        (number, line)
        for number, line in enumerate(text.splitlines(), 1)
        if number not in protected
    ]


def agent_context_leaks(doc: dict, manifest: dict, text: str) -> list[dict]:
    """References from a human-facing document into the agent-context group.

    Returns `{line, target}` records. Agent-context documents are skipped: the
    boundary constrains only the human-facing direction."""
    if doc.get("group") == AGENT_CONTEXT_GROUP:
        return []
    paths, prefixes = agent_context_targets(manifest)
    if not paths:
        return []
    base = PurePosixPath(doc["path"]).parent
    leaks: list[dict] = []
    seen: set[tuple[int, str]] = set()

    def record(number: int, target: str) -> None:
        key = (number, target)
        if key not in seen:
            seen.add(key)
            leaks.append({"line": number, "target": target})

    at_refs = re.compile(
        r"@(" + "|".join(re.escape(path) for path in sorted(paths)) + r")(?![\w./-])"
    )
    for number, line in _unfenced_lines(text):
        for raw in LINK_RE.findall(line):
            target = raw.split("#", 1)[0].strip()
            if not target or target.startswith(("http://", "https://", "mailto:")):
                continue
            resolved = str(PurePosixPath(base / target)) if str(base) != "." else target
            try:
                normalized = PurePosixPath(resolved).as_posix()
            except ValueError:  # pragma: no cover - defensive
                continue
            normalized = _collapse(normalized)
            if _matches(normalized, paths, prefixes):
                record(number, normalized)
        for match in at_refs.finditer(line):
            record(number, match.group(1))
        # Most specific match only: an exact path already names the offending
        # target, so its parent prefix would just repeat the same finding.
        mentioned = [path for path in sorted(paths) if path in line]
        if mentioned:
            for path in mentioned:
                record(number, path)
        else:
            for prefix in sorted(prefixes):
                if prefix in line:
                    record(number, prefix)
    return leaks


def _collapse(path: str) -> str:
    """Resolve `..` segments without touching the filesystem."""
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
