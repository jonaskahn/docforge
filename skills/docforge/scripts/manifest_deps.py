#!/usr/bin/env python3
"""Structured dependency extraction from project-definition manifests.

Shared helper for detect_profiles: turns the file inventory into a per-ecosystem
index of declared dependency identifiers, each mapped to the manifest paths that
declared it. Detection matches a `dependency` signal against this index instead
of substring-scanning raw text, so `torch` no longer bleeds to `torchvision` and
`Django` no longer depends on letter case.

Built-in-only. The Node peer (`manifest_deps.js`) runs the identical algorithm so
`detect_profiles` output stays byte-identical across runtimes. The correctness
bar for the TOML/XML/YAML readers is "extract the declared dependency names",
not "be a conformant parser".
"""

from __future__ import annotations

import json
from pathlib import Path

MAX_MANIFEST_BYTES = 1024 * 1024

ECOSYSTEMS = ["npm", "composer", "pip", "cargo", "go", "gem", "maven", "gradle", "nuget", "pub"]


def normalize(ecosystem: str, name: str) -> str:
    value = name.strip().lower()
    if ecosystem == "pip":
        collapsed = []
        previous_dash = False
        for char in value:
            if char in "-_.":
                if not previous_dash:
                    collapsed.append("-")
                previous_dash = True
            else:
                collapsed.append(char)
                previous_dash = False
        value = "".join(collapsed).strip("-")
    return value


def _read(path: Path) -> str | None:
    try:
        if path.stat().st_size > MAX_MANIFEST_BYTES:
            return None
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None


def _json_keys(text: str, sections: list[str]) -> list[str]:
    names: list[str] = []
    try:
        data = json.loads(text)
    except (ValueError, TypeError):
        return names
    if not isinstance(data, dict):
        return names
    for section in sections:
        table = data.get(section)
        if isinstance(table, dict):
            names.extend(str(key) for key in table.keys())
    return names


def _pep508_name(spec: str) -> str:
    token = spec.strip()
    for cut in (";", " ", "\t"):
        index = token.find(cut)
        if index >= 0:
            token = token[:index]
    stop = len(token)
    for index, char in enumerate(token):
        if not (char.isalnum() or char in "-_."):
            stop = index
            break
    return token[:stop]


def _requirements(text: str) -> list[str]:
    names: list[str] = []
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line or line.startswith("-"):
            continue
        name = _pep508_name(line)
        if name:
            names.append(name)
    return names


def _section_header(line: str) -> str | None:
    stripped = line.strip()
    if stripped.startswith("[") and stripped.endswith("]") and len(stripped) > 2:
        return stripped[1:-1].strip().strip('"').strip("'")
    return None


def _quoted_tokens(text: str) -> list[str]:
    tokens: list[str] = []
    quote = ""
    current: list[str] = []
    for char in text:
        if quote:
            if char == quote:
                tokens.append("".join(current))
                current = []
                quote = ""
            else:
                current.append(char)
        elif char in "\"'":
            quote = char
    return tokens


def _pyproject(text: str) -> list[str]:
    names: list[str] = []
    section = ""
    in_array = False
    for raw in text.splitlines():
        line = raw.split("#", 1)[0]
        header = _section_header(line)
        if header is not None:
            section = header
            in_array = False
            continue
        stripped = line.strip()
        if not stripped:
            continue
        if section == "project":
            key = stripped.split("=", 1)[0].strip()
            if in_array or key == "dependencies":
                if "=" in stripped and key == "dependencies":
                    stripped = stripped.split("=", 1)[1]
                in_array = "]" not in stripped
                for spec in _quoted_tokens(stripped):
                    name = _pep508_name(spec)
                    if name:
                        names.append(name)
        elif section == "project.optional-dependencies":
            body = stripped.split("=", 1)[1] if "=" in stripped else stripped
            for spec in _quoted_tokens(body):
                name = _pep508_name(spec)
                if name:
                    names.append(name)
        elif section.startswith("tool.poetry") and section.endswith("dependencies"):
            key = stripped.split("=", 1)[0].strip().strip('"').strip("'")
            if key and key.lower() != "python":
                names.append(key)
    return names


def _cargo(text: str) -> list[str]:
    names: list[str] = []
    section = ""
    deps = {"dependencies", "dev-dependencies", "build-dependencies"}
    for raw in text.splitlines():
        line = raw.split("#", 1)[0]
        header = _section_header(line)
        if header is not None:
            section = header
            parts = header.split(".")
            for index, part in enumerate(parts):
                if part in deps and index + 1 < len(parts):
                    candidate = parts[index + 1]
                    if candidate and not candidate.startswith("'") and not candidate.startswith('"'):
                        names.append(candidate)
                    break
            continue
        stripped = line.strip()
        if not stripped or section.split(".")[-1] not in deps:
            continue
        key = stripped.split("=", 1)[0].split(".", 1)[0].strip().strip('"').strip("'")
        if key:
            names.append(key)
    return names


def _go_mod(text: str) -> list[str]:
    names: list[str] = []
    in_block = False
    for raw in text.splitlines():
        line = raw.split("//", 1)[0].strip()
        if not line:
            continue
        if in_block:
            if line.startswith(")"):
                in_block = False
                continue
            token = line.split()[0]
            names.append(token)
        elif line.startswith("require ("):
            in_block = True
        elif line.startswith("require "):
            parts = line[len("require "):].strip().split()
            if parts:
                names.append(parts[0])
    return names


def _gemfile(text: str) -> list[str]:
    names: list[str] = []
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line.startswith("gem "):
            continue
        tokens = _quoted_tokens(line)
        if tokens:
            names.append(tokens[0])
    return names


def _inner_text(block: str, tag: str) -> str | None:
    open_tag = "<" + tag
    start = block.find(open_tag)
    if start < 0:
        return None
    gt = block.find(">", start)
    if gt < 0:
        return None
    end = block.find("</" + tag, gt)
    if end < 0:
        return None
    return block[gt + 1:end].strip()


def _blocks(text: str, tag: str) -> list[str]:
    blocks: list[str] = []
    open_tag = "<" + tag
    close_tag = "</" + tag + ">"
    search = 0
    while True:
        start = text.find(open_tag, search)
        if start < 0:
            break
        end = text.find(close_tag, start)
        if end < 0:
            break
        blocks.append(text[start:end + len(close_tag)])
        search = end + len(close_tag)
    return blocks


def _pom(text: str) -> list[str]:
    names: list[str] = []
    for tag in ("dependency", "plugin"):
        for block in _blocks(text, tag):
            group = _inner_text(block, "groupId")
            artifact = _inner_text(block, "artifactId")
            if group:
                names.append(group)
            if group and artifact:
                names.append(group + ":" + artifact)
    return names


def _attr(text: str, attr: str) -> list[str]:
    values: list[str] = []
    needle = attr + "="
    search = 0
    while True:
        index = text.find(needle, search)
        if index < 0:
            break
        rest = text[index + len(needle):].lstrip()
        if rest and rest[0] in "\"'":
            quote = rest[0]
            end = rest.find(quote, 1)
            if end > 0:
                values.append(rest[1:end])
                search = index + len(needle) + end + 1
                continue
        search = index + len(needle)
    return values


def _csproj(text: str) -> list[str]:
    names: list[str] = []
    for value in _attr(text, "Sdk"):
        names.append(value)
    # PackageReference is usually self-closing; scan Include attributes on it.
    search = 0
    while True:
        index = text.find("<PackageReference", search)
        if index < 0:
            break
        gt = text.find(">", index)
        segment = text[index:gt if gt > 0 else len(text)]
        for value in _attr(segment, "Include"):
            names.append(value)
        search = gt + 1 if gt > 0 else len(text)
    return names


def _gradle(text: str) -> list[str]:
    names: list[str] = []
    for raw in text.splitlines():
        line = raw.split("//", 1)[0].strip()
        if not line:
            continue
        tokens = _quoted_tokens(line)
        words = line.replace("(", " ").replace(")", " ").split()
        if "id" in words or "plugin" in line or "plugins" in line:
            for token in tokens:
                names.append(token)
        for token in tokens:
            if ":" in token:
                parts = token.split(":")
                if len(parts) >= 2 and parts[0] and parts[1]:
                    names.append(parts[0] + ":" + parts[1])
                    names.append(parts[0])
    return names


def _pubspec(text: str) -> list[str]:
    names: list[str] = []
    in_deps = False
    for raw in text.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip())
        stripped = raw.strip()
        if indent == 0:
            key = stripped.split(":", 1)[0].strip()
            in_deps = key in {"dependencies", "dev_dependencies"}
            continue
        if in_deps and indent <= 2 and ":" in stripped:
            key = stripped.split(":", 1)[0].strip()
            if key:
                names.append(key)
    return names


def _classify(relative: str, name: str) -> tuple[str, str] | None:
    lower = name.lower()
    if name == "package.json":
        return ("npm", "npm")
    if name == "composer.json":
        return ("composer", "composer")
    if lower.startswith("requirements") and lower.endswith(".txt"):
        return ("pip", "requirements")
    if name == "pyproject.toml":
        return ("pip", "pyproject")
    if name == "Cargo.toml":
        return ("cargo", "cargo")
    if name == "go.mod":
        return ("go", "go")
    if name == "Gemfile":
        return ("gem", "gem")
    if name == "pom.xml":
        return ("maven", "maven")
    if name.endswith(".gradle") or name.endswith(".gradle.kts"):
        return ("gradle", "gradle")
    if name.endswith(".csproj"):
        return ("nuget", "csproj")
    if name in {"pubspec.yaml", "pubspec.yml"}:
        return ("pub", "pubspec")
    return None


_PARSERS = {
    "npm": lambda text: _json_keys(text, ["dependencies", "devDependencies", "peerDependencies", "optionalDependencies"]),
    "composer": lambda text: _json_keys(text, ["require", "require-dev"]),
    "requirements": _requirements,
    "pyproject": _pyproject,
    "cargo": _cargo,
    "go": _go_mod,
    "gem": _gemfile,
    "maven": _pom,
    "csproj": _csproj,
    "gradle": _gradle,
    "pubspec": _pubspec,
}


def extract_dependencies(files: list[tuple[str, Path]]) -> dict:
    """Return {ecosystem: {normalized_name: [manifest_paths]}} from the inventory."""
    index: dict = {}
    for relative, path in files:
        name = Path(relative).name
        classified = _classify(relative, name)
        if classified is None:
            continue
        ecosystem, parser_key = classified
        text = _read(path)
        if text is None:
            continue
        for raw_name in _PARSERS[parser_key](text):
            key = normalize(ecosystem, raw_name)
            if not key:
                continue
            bucket = index.setdefault(ecosystem, {})
            paths = bucket.setdefault(key, [])
            if relative not in paths:
                paths.append(relative)
    for ecosystem in index:
        for key in index[ecosystem]:
            index[ecosystem][key] = sorted(set(index[ecosystem][key]))
    return index
