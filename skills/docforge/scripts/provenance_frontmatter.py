#!/usr/bin/env python3
"""Restricted YAML frontmatter codec for Docforge provenance 2.0.

Emits a deterministic YAML subset (2-space indent, fixed key order, every
scalar double-quoted). Parses that subset plus plain unquoted scalars.
Rejects anchors, aliases, block scalars, multi-document markers, and
non-empty flow collections. Standard library only.
"""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any

SCHEMA_VERSION = "2.0"
LEGACY_SCHEMA = "1.0"
GENERATOR_NAME = "docforge"
GENERATOR_VERSION = "2.1.0"
PROVENANCE_FIELDS = {
    "schema", "doc_id", "path", "generated_at", "generator", "tier",
    "target_depth", "graph", "sections",
}
OPTIONAL_FIELDS = {"git_commit", "content_hash", "review"}
SOURCE_ROLES = {"code", "config", "manifest", "doc", "test", "history"}
FLOW_VALUES = {"native", "derived", "none"}
BLOB = re.compile(r"^[0-9a-f]{40}$")
SCAFFOLD_TOKEN = re.compile(r"^<[A-Z][A-Z0-9_]{2,}>$")
CONTENT_HASH = re.compile(r"^sha256:[0-9a-f]{64}$")
FRONTMATTER = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)

PROVENANCE_KEY_ORDER = [
    "schema", "doc_id", "path", "generated_at", "generator",
    "tier", "target_depth", "git_commit", "content_hash", "review",
    "graph", "sections",
]
GENERATOR_KEY_ORDER = ["name", "version"]
GRAPH_KEY_ORDER = ["provider", "flow"]
SECTION_KEY_ORDER = ["id", "sources", "unresolved"]
SOURCE_KEY_ORDER = ["path", "git_blob", "role"]
REVIEW_KEY_ORDER = ["mode", "verdict", "report"]


class YamlCodecError(ValueError):
    """Raised when restricted YAML cannot be parsed or emitted."""


def quote_scalar(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def content_hash(body: str) -> str:
    digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def scaffold_provenance(
    doc_id: str,
    path: str,
    *,
    tier: str = "<TIER>",
    target_depth: str = "<TARGET_DEPTH>",
    provider: str = "<GRAPH_PROVIDER>",
    flow: str = "<FLOW_CAPABILITY>",
    generated_at: str = "<GENERATED_AT>",
) -> dict:
    return {
        "schema": SCHEMA_VERSION,
        "doc_id": doc_id,
        "path": path,
        "generated_at": generated_at,
        "generator": {"name": GENERATOR_NAME, "version": GENERATOR_VERSION},
        "tier": tier,
        "target_depth": target_depth,
        "graph": {"provider": provider, "flow": flow},
        "sections": [],
    }


def migrate_v1_to_v2(provenance: dict, body: str = "") -> dict:
    if not isinstance(provenance, dict):
        raise YamlCodecError("provenance must be an object")
    schema = provenance.get("schema")
    if schema == SCHEMA_VERSION and "generator" in provenance:
        return dict(provenance)
    if schema != LEGACY_SCHEMA and "tool_version" not in provenance and schema is not None:
        raise YamlCodecError(f"unsupported provenance schema: {schema}")
    tool_version = provenance.get("tool_version") or GENERATOR_VERSION
    if not isinstance(tool_version, str) or not tool_version:
        tool_version = GENERATOR_VERSION
    migrated = {
        "schema": SCHEMA_VERSION,
        "doc_id": provenance.get("doc_id", ""),
        "path": provenance.get("path", ""),
        "generated_at": provenance.get("generated_at", ""),
        "generator": {"name": GENERATOR_NAME, "version": tool_version},
        "tier": provenance.get("tier", ""),
        "target_depth": provenance.get("target_depth", ""),
        "graph": provenance.get("graph") if isinstance(provenance.get("graph"), dict) else {
            "provider": "<GRAPH_PROVIDER>",
            "flow": "<FLOW_CAPABILITY>",
        },
        "sections": provenance.get("sections") if isinstance(provenance.get("sections"), list) else [],
    }
    if isinstance(provenance.get("git_commit"), str):
        migrated["git_commit"] = provenance["git_commit"]
    if isinstance(provenance.get("content_hash"), str):
        migrated["content_hash"] = provenance["content_hash"]
    elif body:
        migrated["content_hash"] = content_hash(body)
    if isinstance(provenance.get("review"), dict):
        migrated["review"] = provenance["review"]
    return migrated


def _emit_mapping(lines: list[str], mapping: dict, key_order: list[str], indent: int) -> None:
    prefix = " " * indent
    for key in key_order:
        if key not in mapping:
            continue
        value = mapping[key]
        if isinstance(value, dict):
            lines.append(f"{prefix}{key}:")
            if key == "generator":
                _emit_mapping(lines, value, GENERATOR_KEY_ORDER, indent + 2)
            elif key == "graph":
                _emit_mapping(lines, value, GRAPH_KEY_ORDER, indent + 2)
            elif key == "review":
                _emit_mapping(lines, value, REVIEW_KEY_ORDER, indent + 2)
            else:
                nested_order = list(value.keys())
                _emit_mapping(lines, value, nested_order, indent + 2)
        elif isinstance(value, list):
            if not value:
                lines.append(f"{prefix}{key}: []")
                continue
            lines.append(f"{prefix}{key}:")
            for item in value:
                if isinstance(item, dict):
                    first = True
                    item_order = (
                        SECTION_KEY_ORDER if "sources" in item
                        else SOURCE_KEY_ORDER if "git_blob" in item
                        else list(item.keys())
                    )
                    for item_key in item_order:
                        if item_key not in item:
                            continue
                        item_value = item[item_key]
                        bullet = "- " if first else "  "
                        first = False
                        if isinstance(item_value, list):
                            if not item_value:
                                lines.append(f"{prefix}  {bullet}{item_key}: []")
                            else:
                                lines.append(f"{prefix}  {bullet}{item_key}:")
                                for nested in item_value:
                                    if isinstance(nested, dict):
                                        nested_first = True
                                        for nested_key in SOURCE_KEY_ORDER:
                                            if nested_key not in nested:
                                                continue
                                            nested_bullet = "- " if nested_first else "  "
                                            nested_first = False
                                            lines.append(
                                                f"{prefix}      {nested_bullet}{nested_key}: "
                                                f"{quote_scalar(str(nested[nested_key]))}"
                                            )
                                    else:
                                        lines.append(
                                            f"{prefix}      - {quote_scalar(str(nested))}"
                                        )
                        else:
                            lines.append(
                                f"{prefix}  {bullet}{item_key}: {quote_scalar(str(item_value))}"
                            )
                else:
                    lines.append(f"{prefix}  - {quote_scalar(str(item))}")
        else:
            lines.append(f"{prefix}{key}: {quote_scalar(str(value))}")


def emit_yaml(provenance: dict) -> str:
    if not isinstance(provenance, dict):
        raise YamlCodecError("provenance must be an object")
    lines = ["---", "docforge_provenance:"]
    _emit_mapping(lines, provenance, PROVENANCE_KEY_ORDER, 2)
    lines.append("---")
    lines.append("")
    return "\n".join(lines)


def wrap_document(provenance: dict, body: str) -> str:
    if body.startswith("\n"):
        return emit_yaml(provenance) + body.lstrip("\n")
    if body and not body.endswith("\n"):
        body = body + "\n"
    return emit_yaml(provenance) + body


def _reject_unsupported(raw: str) -> None:
    for line in raw.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped == "---" or stripped.startswith("..."):
            raise YamlCodecError("unsupported yaml construct: multi-document marker")
        if "&" in stripped or "*" in stripped:
            raise YamlCodecError("unsupported yaml construct: anchor or alias")
        if stripped.endswith("|") or stripped.endswith(">") or stripped.endswith("|-") or stripped.endswith(">-"):
            raise YamlCodecError("unsupported yaml construct: block scalar")
        if re.search(r":\s*[\[{].+[\]}]", stripped):
            raise YamlCodecError("unsupported yaml construct: non-empty flow collection")


def _parse_scalar(raw: str) -> Any:
    value = raw.strip()
    if value == "[]":
        return []
    if value == "{}":
        return {}
    if value in {"null", "~"}:
        return None
    if value in {"true", "false"}:
        return value == "true"
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        if value[0] == '"':
            return json.loads(value)
        return value[1:-1]
    return value


def _indent_of(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def parse_yaml_mapping(raw: str) -> dict:
    _reject_unsupported(raw)
    lines = [line.rstrip("\n") for line in raw.splitlines() if line.strip() and not line.strip().startswith("#")]
    root: dict[str, Any] = {}
    stack: list[tuple[int, Any]] = [(-1, root)]
    i = 0
    while i < len(lines):
        line = lines[i]
        indent = _indent_of(line)
        content = line.strip()
        while len(stack) > 1 and indent <= stack[-1][0]:
            stack.pop()
        parent = stack[-1][1]
        if content.startswith("- "):
            if not isinstance(parent, list):
                raise YamlCodecError("list item without list parent")
            item_content = content[2:]
            if ": " in item_content or item_content.endswith(":"):
                item: dict[str, Any] = {}
                parent.append(item)
                stack.append((indent, item))
                if item_content.endswith(":"):
                    key = item_content[:-1].strip()
                    # Look ahead for nested value or empty list.
                    if i + 1 < len(lines) and _indent_of(lines[i + 1]) > indent:
                        nxt = lines[i + 1].strip()
                        if nxt.startswith("- "):
                            item[key] = []
                            stack.append((indent + 2, item[key]))
                        elif nxt == "[]":
                            i += 1
                            item[key] = []
                        else:
                            item[key] = {}
                            stack.append((indent + 2, item[key]))
                    else:
                        item[key] = {}
                else:
                    key, raw_value = item_content.split(":", 1)
                    item[key.strip()] = _parse_scalar(raw_value)
            else:
                parent.append(_parse_scalar(item_content))
            i += 1
            continue
        if ": " in content or content.endswith(":"):
            if not isinstance(parent, dict):
                raise YamlCodecError("mapping entry without mapping parent")
            if content.endswith(":"):
                key = content[:-1].strip()
                if i + 1 < len(lines) and _indent_of(lines[i + 1]) > indent:
                    nxt = lines[i + 1].strip()
                    if nxt == "[]":
                        i += 1
                        parent[key] = []
                    elif nxt.startswith("- "):
                        parent[key] = []
                        stack.append((indent, parent[key]))
                    else:
                        parent[key] = {}
                        stack.append((indent, parent[key]))
                else:
                    parent[key] = {}
            else:
                key, raw_value = content.split(":", 1)
                parent[key.strip()] = _parse_scalar(raw_value)
            i += 1
            continue
        raise YamlCodecError(f"unsupported yaml construct: {content}")
    return root


def split_frontmatter(text: str) -> tuple[str | None, str, int]:
    match = FRONTMATTER.match(text)
    if not match:
        return None, text, 0
    return match.group(1), text[match.end():], match.end()


def parse_frontmatter(text: str) -> tuple[str, dict | None, int]:
    """Return (state, provenance_or_none, body_start).

    States: missing, unparseable, legacy, obsolete, ok.
    """
    raw, _body, end = split_frontmatter(text)
    if raw is None:
        return "missing", None, 0
    stripped = raw.lstrip()
    if stripped.startswith("{"):
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return "unparseable", None, end
        provenance = data.get("docforge_provenance") if isinstance(data, dict) else None
        if not isinstance(provenance, dict):
            return "missing", None, end
        if "schema" not in provenance:
            return "legacy", provenance, end
        if provenance.get("schema") == LEGACY_SCHEMA or "tool_version" in provenance:
            return "obsolete", provenance, end
        return "obsolete", provenance, end
    try:
        data = parse_yaml_mapping(raw)
    except YamlCodecError:
        return "unparseable", None, end
    provenance = data.get("docforge_provenance") if isinstance(data, dict) else None
    if not isinstance(provenance, dict):
        return "missing", None, end
    if "schema" not in provenance:
        return "legacy", provenance, end
    if provenance.get("schema") != SCHEMA_VERSION or "tool_version" in provenance:
        return "obsolete", provenance, end
    return "ok", provenance, end


def rewrite_frontmatter(text: str, provenance: dict) -> str:
    raw, body, _end = split_frontmatter(text)
    if raw is None:
        return wrap_document(provenance, text)
    return emit_yaml(provenance) + body
