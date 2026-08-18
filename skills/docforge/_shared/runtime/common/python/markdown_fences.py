"""Small CommonMark-compatible fence scanner shared by Docforge tools."""

from __future__ import annotations

import re

OPEN_RE = re.compile(r"^\s{0,3}(?P<marker>`{3,}|~{3,})(?P<info>[^`]*)$")
SOURCE_LINK_RE = re.compile(r"\[[^\]]+\]\((?P<target>[^)]+\.(?:c|cc|cpp|cs|go|java|js|jsx|json|mjs|properties|py|rb|rs|swift|toml|ts|tsx|xml|ya?ml)(?:#[^)]+)?)\)")
SOURCE_LINE_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_./-]*\.(?:c|cc|cpp|cs|go|java|js|jsx|json|mjs|properties|py|rb|rs|swift|toml|ts|tsx|xml|ya?ml)(?:#L\d+(?:-L\d+)?|:\d+(?:-\d+)?)(?!\s*@\s*[0-9a-f]{40})\b")
LOCATOR_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_./-]*#L\d+(?:-L\d+)?\s*@\s*[0-9a-f]{40}")
SHELL_LANGUAGES = {"bash", "sh", "shell", "zsh", "fish", "powershell", "pwsh"}


def scan_fences(text: str) -> list[dict]:
    """Return closed and unclosed fences with zero ambiguity about protected lines."""
    fences: list[dict] = []
    current: dict | None = None
    for number, line in enumerate(text.splitlines(), 1):
        match = OPEN_RE.match(line)
        if current is None:
            if not match:
                continue
            info = match.group("info").strip().split()
            language = info[0] if info else ""
            role = next((part.split("=", 1)[1] for part in info[1:] if part.startswith("docforge-role=")), None)
            current = {
                "start": number,
                "marker": match.group("marker"),
                "language": language,
                "role": role or inferred_role(language),
                "explicit_role": role,
                "lines": [],
            }
            continue
        if match and match.group("marker")[0] == current["marker"][0] and len(match.group("marker")) >= len(current["marker"]):
            current["end"] = number
            fences.append(current)
            current = None
        else:
            current["lines"].append((number, line))
    if current is not None:
        current["end"] = None
        fences.append(current)
    return fences


def inferred_role(language: str) -> str:
    if language == "mermaid":
        return "diagram"
    if language in SHELL_LANGUAGES:
        return "command"
    if language in {"markdown", "mdx"}:
        return "markup"
    if language in {"text", "ascii", "console", ""}:
        return "ambiguous"
    return "code"


def visible_presentation_defects(text: str) -> list[dict]:
    defects: list[dict] = []
    fences = scan_fences(text)
    fenced_lines = {number for fence in fences for number, _ in fence["lines"]}
    for number, line in enumerate(text.splitlines(), 1):
        if number in fenced_lines:
            continue
        if LOCATOR_RE.search(line):
            defects.append({"kind": "visible-source-locator", "line": number, "detail": "use provenance, not a path/range/blob citation"})
        for match in SOURCE_LINK_RE.finditer(line):
            defects.append({"kind": "source-code-link", "line": number, "detail": match.group("target")})
        for match in SOURCE_LINE_RE.finditer(line):
            defects.append({"kind": "visible-source-line", "line": number, "detail": match.group(0)})
    for fence in fences:
        if fence["role"] not in {"command", "code", "diagram", "structure", "ambiguous"}:
            continue
        content = [line.strip() for _, line in fence["lines"] if line.strip()]
        words = sum(len(re.findall(r"[A-Za-z]{2,}", line)) for line in content)
        sentence_lines = [line for line in content if re.search(r"[.!?][\"')\]]?$", line)]
        syntax_lines = [line for line in content if re.search(r"[{};]|=>|\$ |^[-+]?\w+[=:]|\|", line)]
        if (
            len(content) >= 2
            and words >= 20
            and len(sentence_lines) / len(content) >= 0.7
            and len(syntax_lines) / len(content) < 0.3
        ):
            defects.append({
                "kind": "prose-in-code-fence",
                "line": fence["start"],
                "detail": f"{fence['role']} fence contains explanatory prose",
            })
    return defects
