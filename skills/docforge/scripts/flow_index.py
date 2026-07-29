#!/usr/bin/env python3
"""Harvest, rank, revise, organize, and render Docforge's repository flow index.

Understand Anything JSON is read directly. GitNexus is consumed through a
small JSON export produced by its MCP/cypher interface, keeping this tool
standard-library-only and equivalent to its Node peer.

  python flow_index.py harvest --repo <repo> [--gitnexus-export <json>]
  python flow_index.py revise --repo <repo> [--gitnexus-export <json>]
  python flow_index.py organize emit --repo <repo>
  python flow_index.py organize apply --repo <repo> --organization <json>
  python flow_index.py render --repo <repo>
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from provenance_frontmatter import emit_yaml, scaffold_provenance

INDEX_REL = Path(".docforge/flow-index.json")
TMP_REL = Path(".docforge/tmp")
ORG_PACK_REL = TMP_REL / "flow-organization-pack.json"
UA_DIRS = (".ua", ".understand-anything")
INDEX_VERSION = "1.1"
BARE_VERBS = frozenset({
    "get", "save", "create", "update", "delete", "execute", "init", "count",
    "publish", "verify", "connect", "archive", "resend", "authorize", "send",
    "post", "put", "patch", "run", "start", "handle", "process", "dispatch",
    "receive", "consume", "track", "aggregate",
})
ENTRY_WORDS = re.compile(
    r"^(?:[Aa]ggregate|[Tt]rack|[Pp]ublish|[Dd]ispatch|[Ee]xecute|"
    r"[Rr]un|[Ss]tart|[Rr]eceive|[Pp]rocess|[Cc]onsume|[Hh]andle|"
    r"[Cc]reate|[Uu]pdate|[Dd]elete|[Ss]ave|[Gg]et|[Pp]ost|[Pp]ut|"
    r"[Pp]atch|[Ss]end)(?:[A-Z0-9_]|$)",
)
CORE_ENTRY_WORDS = re.compile(
    r"^(?:[Aa]ggregate|[Tt]rack|[Pp]ublish|[Dd]ispatch|[Ee]xecute|"
    r"[Rr]un|[Ss]tart|[Rr]eceive|[Pp]rocess|[Cc]onsume|[Hh]andle)"
    r"(?:[A-Z0-9_]|$)",
)
SURFACE_WORDS = re.compile(
    r"(controller|handler|processor|consumer|listener|worker|job|command|aggregator)$",
    re.IGNORECASE,
)
PATH_WORDS = re.compile(
    r"(controllers?|handlers?|processors?|consumers?|workers?|jobs?|commands?|"
    r"aggregators?|routes?|endpoints?)",
    re.IGNORECASE,
)
FAMILY_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
FLOW_ID_RE = re.compile(r"^flow-[a-z0-9][a-z0-9-]*$")
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def fail(message: str, code: int = 1) -> int:
    print(f"error: {message}", file=sys.stderr)
    return code


def read_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise ValueError(f"file not found: {path}") from error
    except json.JSONDecodeError as error:
        raise ValueError(f"invalid JSON in {path}: {error}") from error
    if not isinstance(value, dict):
        raise ValueError(f"expected a JSON object: {path}")
    return value


def find_ua(repo: Path, name: str) -> Path | None:
    for directory in UA_DIRS:
        path = repo / directory / name
        if path.is_file():
            return path
    return None


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug[:80] or "unnamed-flow"


def split_symbol_id(value: str | None) -> tuple[str | None, str | None]:
    if not value:
        return None, None
    parts = str(value).split(":")
    if len(parts) >= 3:
        return parts[1], parts[-1]
    return None, parts[-1]


def module_from_path(file_path: str | None) -> str | None:
    if not file_path:
        return None
    normalized = str(file_path).replace("\\", "/")
    match = re.search(r"(?:^|/)(?:src/)?modules/([^/]+)", normalized)
    if match:
        return slugify(match.group(1))
    match = re.search(r"(?:^|/)src/([^/]+)/", normalized)
    if match:
        segment = match.group(1).lower()
        if segment not in {"lib", "utils", "common", "shared", "helpers", "types"}:
            return slugify(segment)
    return None


def base_slug_for(row: dict) -> str:
    name = str(row.get("name") or "")
    base = slugify(name)
    symbol = str(row.get("entry_ref", {}).get("symbol") or name)
    symbol_slug = slugify(symbol)
    if base in BARE_VERBS or symbol_slug in BARE_VERBS:
        module = module_from_path(row.get("entry_ref", {}).get("filePath"))
        if module:
            return f"{module}-{base}"
    return base


def infer_kind(signature: str, path: str | None = None) -> str:
    text = f"{signature} {path or ''}".lower()
    if re.search(r"\b(get|post|put|patch|delete)\b|/api/|controller|handler|route", text):
        return "http"
    if "queue" in text or "consumer" in text or "listener" in text:
        return "queue"
    if "cron" in text or "schedule" in text or "job" in text:
        return "schedule"
    if "command" in text or "cli" in text:
        return "cli"
    if re.search(r"screen|view|component|page", text):
        return "ui"
    return "internal"


def normalize_kind(value: str | None, signature: str, path: str | None = None) -> str:
    raw = str(value or "").lower()
    aliases = {
        "http": "http", "api": "http", "web": "http",
        "queue": "queue", "event": "queue", "message": "queue",
        "schedule": "schedule", "scheduled": "schedule", "cron": "schedule", "timer": "schedule",
        "cli": "cli", "command": "cli",
        "ui": "ui", "screen": "ui",
        "internal": "internal",
    }
    return aliases.get(raw, infer_kind(signature, path))


def candidate(
    *,
    name: str,
    kind: str,
    signature: str,
    file_path: str | None,
    symbol: str | None,
    area: str | None,
    evidence: dict,
    confidence: str = "candidate",
    steps: int = 0,
    boundaries: int = 0,
) -> dict:
    return {
        "name": name,
        "entry_ref": {
            "kind": kind,
            "signature": signature,
            "filePath": file_path,
            "symbol": symbol,
        },
        "area": area or "Unclassified",
        "evidence": [evidence],
        "confidence": confidence,
        "reach": {"steps": int(steps or 0), "boundaries": int(boundaries or 0), "churn": 0},
    }


def harvest_ua_domain(path: Path) -> list[dict]:
    doc = read_json(path)
    nodes = doc.get("nodes") or []
    edges = doc.get("edges") or []
    by_id = {node.get("id"): node for node in nodes if isinstance(node, dict)}
    domain_for: dict[str, str] = {}
    domain_id_for: dict[str, str] = {}
    step_for: dict[str, list[dict]] = {}
    for edge in edges:
        if not isinstance(edge, dict):
            continue
        if edge.get("type") == "contains_flow":
            domain = by_id.get(edge.get("source"), {})
            domain_for[edge.get("target")] = domain.get("name") or "Unclassified"
            domain_id_for[edge.get("target")] = edge.get("source")
        elif edge.get("type") == "flow_step":
            step = by_id.get(edge.get("target"))
            if step:
                step_for.setdefault(edge.get("source"), []).append(step)
    rows = []
    for flow in nodes:
        if not isinstance(flow, dict) or flow.get("type") != "flow":
            continue
        meta = flow.get("domainMeta") or {}
        steps = step_for.get(flow.get("id"), [])
        first = steps[0] if steps else {}
        signature = str(meta.get("entryPoint") or flow.get("name") or flow.get("id"))
        file_path = first.get("filePath")
        domain_id = domain_id_for.get(flow.get("id"))
        crosses = any(
            edge.get("type") == "cross_domain"
            and domain_id in (edge.get("source"), edge.get("target"))
            for edge in edges if isinstance(edge, dict)
        )
        rows.append(candidate(
            name=str(flow.get("name") or signature),
            kind=normalize_kind(meta.get("entryType"), signature, file_path),
            signature=signature,
            file_path=file_path,
            symbol=None,
            area=domain_for.get(flow.get("id")),
            evidence={"provider": "understand-anything", "artifact": str(path), "nodeId": flow.get("id")},
            confidence="confirmed",
            steps=len(steps),
            boundaries=1 if crosses else 0,
        ))
    return rows


def harvest_ua_knowledge(path: Path) -> list[dict]:
    doc = read_json(path)
    nodes = [node for node in doc.get("nodes", []) if isinstance(node, dict)]
    area_by_id: dict[str, str] = {}
    for layer in doc.get("layers", []):
        if not isinstance(layer, dict):
            continue
        layer_name = str(layer.get("name") or "")
        if not any(word in layer_name.lower() for word in ("presentation", "api", "application", "service")):
            continue
        for node_id in layer.get("nodeIds") or []:
            area_by_id[node_id] = layer_name

    rows = []
    seen: set[str] = set()
    for node in nodes:
        node_id = node.get("id")
        name = str(node.get("name") or "")
        file_path = node.get("filePath")
        in_entry_layer = node_id in area_by_id
        path_signal = bool(file_path and PATH_WORDS.search(str(file_path)))
        is_surface_class = (
            node.get("type") == "class"
            and (in_entry_layer or path_signal)
            and SURFACE_WORDS.search(name)
        )
        is_entry_function = (
            node.get("type") == "function"
            and (
                (path_signal and ENTRY_WORDS.search(name))
                or (in_entry_layer and CORE_ENTRY_WORDS.search(name))
            )
        )
        if not (is_surface_class or is_entry_function):
            continue
        key = f"{file_path}:{name}".lower()
        if key in seen:
            continue
        seen.add(key)
        rows.append(candidate(
            name=name,
            kind=infer_kind(name, file_path),
            signature=name,
            file_path=file_path,
            symbol=name,
            area=area_by_id.get(node_id),
            evidence={"provider": "understand-anything", "artifact": str(path), "nodeId": node_id},
        ))
    return rows


def harvest_gitnexus(path: Path) -> list[dict]:
    """Read an MCP export: {routes:[], processes:[], communities:[]}."""
    doc = read_json(path)
    communities = {
        str(item.get("id")): item.get("heuristicLabel") or item.get("name")
        for item in doc.get("communities", []) if isinstance(item, dict)
    }
    rows: list[dict] = []
    for route in doc.get("routes", []):
        if not isinstance(route, dict):
            continue
        signature = str(route.get("path") or route.get("route") or route.get("name") or route.get("id"))
        file_path = route.get("filePath")
        rows.append(candidate(
            name=str(route.get("name") or signature),
            kind="http",
            signature=signature,
            file_path=file_path,
            symbol=route.get("symbol"),
            area=route.get("communityLabel"),
            evidence={"provider": "gitnexus", "artifact": str(path), "nodeId": route.get("id")},
            steps=1,
        ))

    grouped: dict[str, list[dict]] = {}
    for process in doc.get("processes", []):
        if isinstance(process, dict):
            entry = process.get("entryPointId") or process.get("entry_point_id")
            if entry:
                grouped.setdefault(str(entry), []).append(process)
    for entry_id, processes in grouped.items():
        file_path, symbol = split_symbol_id(entry_id)
        terminals = sorted({
            str(item.get("terminalId") or item.get("terminal_id"))
            for item in processes if item.get("terminalId") or item.get("terminal_id")
        })
        community_ids = {
            str(value).strip("'")
            for item in processes for value in (item.get("communities") or [])
        }
        labels = sorted({
            str(communities[value])
            for value in community_ids
            if communities.get(value)
        })
        cross = any(
            item.get("processType") == "cross_community"
            or item.get("process_type") == "cross_community"
            for item in processes
        )
        name = str(symbol or processes[0].get("heuristicLabel") or entry_id)
        rows.append(candidate(
            name=name,
            kind=infer_kind(name, file_path),
            signature=entry_id,
            file_path=file_path,
            symbol=symbol,
            area=", ".join(labels) or processes[0].get("communityLabel"),
            evidence={
                "provider": "gitnexus",
                "artifact": str(path),
                "nodeId": entry_id,
                "processIds": sorted(str(item.get("id")) for item in processes if item.get("id")),
                "terminalIds": terminals,
            },
            steps=max(int(item.get("stepCount") or item.get("steps") or 0) for item in processes),
            boundaries=max(len(community_ids) - 1, 1 if cross else 0),
        ))
    return rows


def unique_area(*areas: str | None) -> str:
    labels: list[str] = []
    seen: set[str] = set()
    for area in areas:
        if not area or area == "Unclassified":
            continue
        for part in str(area).split(","):
            label = part.strip()
            key = label.lower()
            if label and key not in seen:
                seen.add(key)
                labels.append(label)
    return ", ".join(sorted(labels, key=str.lower)) or "Unclassified"


def row_key(row: dict) -> str:
    entry = row["entry_ref"]
    if entry.get("filePath") and entry.get("symbol"):
        return f"{entry['filePath']}::{entry['symbol']}".lower()
    return f"{entry.get('kind')}::{entry.get('signature')}".lower()


def near_key(row: dict) -> str:
    """Secondary merge key: same path+name slug, else normalized signature."""
    entry = row["entry_ref"]
    file_path = str(entry.get("filePath") or "").replace("\\", "/").lower().strip()
    name_slug = slugify(row["name"])
    if file_path and name_slug:
        return f"path+name::{file_path}::{name_slug}"
    signature = str(entry.get("signature") or "").lower().strip()
    if signature:
        return f"sig::{signature}"
    return f"exact::{row_key(row)}"


def fold_row(current: dict, row: dict) -> None:
    current["evidence"].extend(
        item for item in row["evidence"] if item not in current["evidence"]
    )
    if row["confidence"] == "confirmed":
        current["confidence"] = "confirmed"
        current["name"] = row["name"]
        current["entry_ref"] = row["entry_ref"]
    current["reach"]["steps"] = max(current["reach"]["steps"], row["reach"]["steps"])
    current["reach"]["boundaries"] = max(
        current["reach"]["boundaries"], row["reach"]["boundaries"]
    )
    current["reach"]["churn"] = max(
        current["reach"].get("churn", 0), row["reach"].get("churn", 0)
    )
    current["area"] = unique_area(current.get("area"), row.get("area"))


def merge_rows(rows: list[dict]) -> list[dict]:
    """Exact-key merge, then near-duplicate merge (path+name / signature)."""
    merged: dict[str, dict] = {}
    for row in rows:
        key = row_key(row)
        if key not in merged:
            merged[key] = row
            continue
        fold_row(merged[key], row)
    exact = list(merged.values())
    near: dict[str, dict] = {}
    for row in exact:
        key = near_key(row)
        if key not in near:
            near[key] = row
            continue
        fold_row(near[key], row)
    return list(near.values())


def write_communities_summary(repo: Path, export_path: Path) -> Path:
    """Compact unique-label community table for agent/LLM context."""
    from graph_storage import ensure_tmp_dir_gitignored

    doc = read_json(export_path)
    by_label: dict[str, list[str]] = {}
    for item in doc.get("communities") or []:
        if not isinstance(item, dict):
            continue
        community_id = str(item.get("id") or "").strip()
        if not community_id:
            continue
        label = str(item.get("heuristicLabel") or item.get("name") or community_id)
        by_label.setdefault(label, []).append(community_id)
    ensure_tmp_dir_gitignored(repo)
    tmp = repo.resolve() / TMP_REL
    lines = [
        "# Communities (deduplicated by label)",
        "",
        "Community IDs remain distinct for reach/boundary math; labels are",
        "collapsed here so agent flow analysis is not flooded by duplicates.",
        "",
        "| Label | Count | Community IDs |",
        "| --- | --- | --- |",
    ]
    payload = []
    for label in sorted(by_label, key=str.lower):
        ids = sorted(by_label[label])
        payload.append({"label": label, "count": len(ids), "ids": ids})
        shown = ", ".join(ids[:12])
        if len(ids) > 12:
            shown += f", … (+{len(ids) - 12})"
        lines.append(f"| {label.replace('|', '\\|')} | {len(ids)} | {shown} |")
    lines += ["", f"_Source: `{export_path}`_", ""]
    markdown_path = tmp / "communities.md"
    json_path = tmp / "communities.json"
    markdown_path.write_text("\n".join(lines), encoding="utf-8")
    json_path.write_text(
        json.dumps({"version": "1.0", "labels": payload}, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return markdown_path


def score(row: dict) -> int:
    kind_scores = {"http": 400, "queue": 350, "schedule": 300, "cli": 280, "ui": 250, "internal": 80}
    return (
        kind_scores.get(row["entry_ref"]["kind"], 0)
        + (600 if row["confidence"] == "confirmed" else 0)
        + (150 if SURFACE_WORDS.search(row["name"]) else 0)
        + min(row["reach"]["boundaries"], 5) * 80
        + min(row["reach"]["steps"], 20) * 5
        + min(row["reach"].get("churn", 0), 20) * 2
        + min(len(row["evidence"]), 3) * 20
    )


def add_churn(repo: Path, rows: list[dict]) -> None:
    try:
        result = subprocess.run(
            ["git", "-C", str(repo), "log", "-n", "200", "--name-only", "--pretty=format:"],
            text=True,
            capture_output=True,
            check=False,
        )
    except OSError:
        return
    if result.returncode != 0:
        return
    counts: dict[str, int] = {}
    for line in result.stdout.splitlines():
        relative = line.strip().replace("\\", "/")
        if relative:
            counts[relative] = counts.get(relative, 0) + 1
    for row in rows:
        file_path = row["entry_ref"].get("filePath")
        row["reach"]["churn"] = counts.get(str(file_path).replace("\\", "/"), 0) if file_path else 0


def default_doc_path(slug: str, family: str | None = None) -> str:
    if family:
        return f"docs/flows/{family}/{slug}.md"
    return f"docs/flows/{slug}.md"


def apply_org_defaults(row: dict) -> None:
    """Fill organization fields for harvest/revise rows."""
    priority = row.get("priority") or row_priority(row) or "deferred"
    if "display_name" not in row or not row.get("display_name"):
        row["display_name"] = row.get("name") or row.get("slug") or "unnamed"
    if "family" not in row:
        row["family"] = None
    if "composed_into" not in row:
        row["composed_into"] = None
    if row.get("doc_role") not in {"standalone", "member", "index_only"}:
        if priority == "main":
            row["doc_role"] = "standalone"
        else:
            row["doc_role"] = "index_only"
    if row["doc_role"] in {"member", "index_only"}:
        row["doc_path"] = None
    elif not row.get("doc_path"):
        row["doc_path"] = default_doc_path(row["slug"], row.get("family"))


def finalize(rows: list[dict], main_limit: int, repo: Path | None = None) -> list[dict]:
    rows = merge_rows(rows)
    if repo is not None:
        add_churn(repo, rows)
    for row in rows:
        row["rank"] = score(row)
    rows.sort(key=lambda item: (-item["rank"], item["name"].lower(), row_key(item)))
    used: dict[str, int] = {}
    for index, row in enumerate(rows):
        base = base_slug_for(row)
        used[base] = used.get(base, 0) + 1
        slug = base if used[base] == 1 else f"{base}-{used[base]}"
        row["slug"] = slug
        row["id"] = f"flow-{slug}"
        priority = "main" if index < max(main_limit, 0) else "deferred"
        row["priority"] = priority
        row["status"] = priority
        row["display_name"] = row.get("name") or slug
        row["family"] = None
        row["composed_into"] = None
        row["doc_role"] = "standalone" if priority == "main" else "index_only"
        row["doc_path"] = default_doc_path(slug) if priority == "main" else None
    return rows


def load_existing_index(repo: Path) -> dict | None:
    path = repo / INDEX_REL
    if not path.is_file():
        return None
    try:
        return read_json(path)
    except ValueError:
        return None


def prior_by_key(existing: dict | None) -> dict[str, dict]:
    if not existing:
        return {}
    return {row_key(row): row for row in existing.get("flows", []) if isinstance(row, dict)}


def apply_revise_statuses(rows: list[dict], prior: dict[str, dict]) -> list[dict]:
    """Preserve documented/skipped and organization fields; mark else placeholder."""
    org_keys = ("display_name", "family", "doc_role", "composed_into", "doc_path")
    for row in rows:
        previous = prior.get(row_key(row))
        if previous is None:
            row["status"] = "placeholder"
            apply_org_defaults(row)
            continue
        prior_status = previous.get("status")
        if prior_status in {"documented", "skipped"}:
            row["status"] = prior_status
            if previous.get("slug"):
                row["slug"] = previous["slug"]
                row["id"] = previous.get("id") or f"flow-{previous['slug']}"
            if previous.get("priority") in {"main", "deferred"}:
                row["priority"] = previous["priority"]
        else:
            row["status"] = "placeholder"
            if previous.get("slug") and (previous.get("status") in {"placeholder", "main", "deferred"}):
                row["slug"] = previous["slug"]
                row["id"] = previous.get("id") or f"flow-{previous['slug']}"
        for key in org_keys:
            if key in previous and previous[key] is not None:
                row[key] = previous[key]
            elif key in previous and key in {"family", "composed_into", "doc_path"}:
                row[key] = previous[key]
        apply_org_defaults(row)
        # Members / index_only never keep a stub path.
        if row.get("doc_role") in {"member", "index_only"}:
            row["doc_path"] = None
        elif row.get("priority") == "main" and not row.get("doc_path"):
            row["doc_path"] = default_doc_path(row["slug"], row.get("family"))
    return rows


def row_priority(row: dict) -> str | None:
    if row.get("priority") in {"main", "deferred"}:
        return row["priority"]
    if row.get("status") in {"main", "deferred"}:
        return row["status"]
    return None


def summary_for(rows: list[dict]) -> dict:
    return {
        "total": len(rows),
        "main": sum(row_priority(row) == "main" for row in rows),
        "deferred": sum(row_priority(row) == "deferred" for row in rows),
        "placeholder": sum(row["status"] == "placeholder" for row in rows),
        "documented": sum(row["status"] == "documented" for row in rows),
        "skipped": sum(row["status"] == "skipped" for row in rows),
        "confirmed": sum(row["confidence"] == "confirmed" for row in rows),
    }


def write_index(repo: Path, rows: list[dict], sources: list[str]) -> Path:
    for row in rows:
        apply_org_defaults(row)
    providers = sorted({e["provider"] for row in rows for e in row["evidence"]})
    value = {
        "version": INDEX_VERSION,
        "generated_at": now_iso(),
        "project": repo.resolve().name,
        "sources": sources,
        "providers": providers,
        "summary": summary_for(rows),
        "flows": rows,
    }
    path = repo / INDEX_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def resolve_doc_path(row: dict) -> str | None:
    if row.get("doc_path"):
        return str(row["doc_path"]).replace("\\", "/")
    if row.get("doc_role") in {"member", "index_only"}:
        return None
    if row.get("priority") == "main" or row.get("status") == "documented":
        return default_doc_path(row["slug"], row.get("family"))
    return None


def stub_body(row: dict) -> str:
    name = row.get("display_name") or row["name"]
    doc_path = resolve_doc_path(row) or default_doc_path(row["slug"], row.get("family"))
    entry = row["entry_ref"]
    signature = entry.get("signature") or name
    provenance = scaffold_provenance(
        row["id"],
        doc_path,
        tier="diligence",
        target_depth="deep-dive",
        provider="unknown",
        flow="derived",
        generated_at=now_iso(),
    )
    return emit_yaml(provenance) + "\n".join([
        f"# {name}",
        "",
        "_Last reviewed: {{YYYY-MM-DD}}_",
        "",
        f"Placeholder flow candidate for `{signature}`.",
        "",
        "Status: `placeholder` — awaiting full flow documentation.",
        "",
        f"- Area: {row.get('area') or 'Unclassified'}",
        f"- Family: {row.get('family') or '—'}",
        f"- Trigger kind: {entry.get('kind')}",
        f"- Entry: `{signature}`",
        "",
        "{{Write this document from the evidence required by its catalog entry.}}",
        "",
    ])


def is_scaffold_or_placeholder(text: str) -> bool:
    return (
        "{{" in text
        or "TODO(" in text
        or "Status: `placeholder`" in text
        or "<DOC_ID>" in text
    )


def should_stub(row: dict) -> bool:
    if row["status"] != "placeholder":
        return False
    if row.get("priority") != "main":
        return False
    if row.get("doc_role") in {"member", "index_only"}:
        return False
    return True


def ensure_stubs(repo: Path, rows: list[dict]) -> list[dict]:
    """Create stub markdown for main-priority standalone placeholders only."""
    created: list[dict] = []
    for row in rows:
        if not should_stub(row):
            continue
        rel = resolve_doc_path(row) or default_doc_path(row["slug"], row.get("family"))
        row["doc_path"] = rel
        target = repo / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.is_file():
            existing = target.read_text(encoding="utf-8")
            if not is_scaffold_or_placeholder(existing):
                continue
        target.write_text(stub_body(row), encoding="utf-8")
        created.append({
            "id": row["id"],
            "slug": row["slug"],
            "path": rel,
            "priority": row.get("priority", "deferred"),
            "name": row.get("display_name") or row["name"],
        })
    return created


def prune_orphan_stubs(repo: Path, rows: list[dict]) -> list[str]:
    """Delete scaffold stubs that are not main standalone/documented targets."""
    keep: set[str] = set()
    for row in rows:
        if row.get("doc_role") in {"member", "index_only"}:
            continue
        if row.get("status") == "documented" or (
            row.get("priority") == "main" and row.get("doc_role") == "standalone"
        ):
            rel = resolve_doc_path(row)
            if rel:
                keep.add(rel.replace("\\", "/"))

    flows_dir = repo / "docs" / "flows"
    if not flows_dir.is_dir():
        return []
    removed: list[str] = []
    for path in flows_dir.rglob("*.md"):
        rel = path.relative_to(repo).as_posix()
        if path.name == "README.md":
            continue
        if rel in keep:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        if not is_scaffold_or_placeholder(text):
            continue
        path.unlink()
        removed.append(rel)
        # Remove empty family directories.
        parent = path.parent
        if parent != flows_dir and parent.is_dir() and not any(parent.iterdir()):
            parent.rmdir()
    return removed


def flow_doc_exists(repo: Path | None, row_or_slug) -> bool:
    if repo is None:
        return False
    if isinstance(row_or_slug, dict):
        rel = resolve_doc_path(row_or_slug)
        if not rel:
            return False
        return (repo / rel).is_file()
    return (repo / "docs" / "flows" / f"{row_or_slug}.md").is_file()


def link_for_row(row: dict) -> str:
    name = (row.get("display_name") or row["name"]).replace("|", "\\|")
    rel = resolve_doc_path(row)
    if not rel:
        return name
    # README lives at docs/flows/README.md — link relative to that.
    link = rel
    if link.startswith("docs/flows/"):
        link = "./" + link[len("docs/flows/"):]
    else:
        link = "./" + Path(link).name
    return f"[{name}]({link})"


def markdown(index: dict, tier: str = "spine", repo: Path | None = None) -> str:
    generated = index["generated_at"]
    provider = ", ".join(index.get("providers") or []) or "unknown"
    provenance = scaffold_provenance(
        "flows_index",
        "docs/flows/README.md",
        tier=tier,
        target_depth="orientation",
        provider=provider,
        flow="none",
        generated_at=generated,
    )
    lines = [
        "# Flow index",
        "",
        "This is the complete evidence-backed flow candidate index. `main` priority",
        "standalone rows get deep-dive documentation; `member` rows are composed into",
        "a parent; `index_only` / deferred rows stay discoverable without stub files.",
        "",
    ]

    flows = [row for row in index.get("flows", []) if isinstance(row, dict)]
    families: dict[str, list[dict]] = {}
    ungrouped: list[dict] = []
    for row in flows:
        family = row.get("family")
        if family:
            families.setdefault(str(family), []).append(row)
        else:
            ungrouped.append(row)

    def append_table(rows: list[dict]) -> None:
        lines.append("| Status | Role | Flow | Trigger | Entry point | Area | Confidence | Reach |")
        lines.append("|---|---|---|---|---|---|---|---|")
        for row in rows:
            entry = row["entry_ref"]
            name = row.get("display_name") or row["name"]
            if row["status"] in {"documented", "placeholder"} and flow_doc_exists(repo, row):
                name = link_for_row(row)
            elif row["status"] == "documented":
                name = link_for_row(row)
            else:
                name = str(name).replace("|", "\\|")
            if row.get("doc_role") == "member" and row.get("composed_into"):
                name = f"{name} → `{row['composed_into']}`"
            signature = str(entry.get("signature") or "").replace("|", "\\|")
            area = str(row.get("area") or "").replace("|", "\\|")
            reach = (
                f"{row['reach']['steps']} steps / {row['reach']['boundaries']} boundaries / "
                f"{row['reach'].get('churn', 0)} changes"
            )
            lines.append(
                f"| {row['status']} | {row.get('doc_role', '—')} | {name} | {entry['kind']} | "
                f"`{signature}` | {area} | {row['confidence']} | {reach} |"
            )
        lines.append("")

    for family in sorted(families):
        lines += [f"## {family}", ""]
        append_table(families[family])
    if ungrouped:
        if families:
            lines += ["## Ungrouped", ""]
        append_table(ungrouped)

    lines += [
        f"_Generated {generated}; source of truth: `.docforge/flow-index.json`._",
        "",
    ]
    return emit_yaml(provenance) + "\n".join(lines)


def collect_candidates(args: argparse.Namespace) -> tuple[list[dict], list[str], Path | None]:
    rows: list[dict] = []
    sources: list[str] = []
    gitnexus_export: Path | None = None
    domain = find_ua(args.repo, "domain-graph.json")
    knowledge = find_ua(args.repo, "knowledge-graph.json")
    if domain:
        rows.extend(harvest_ua_domain(domain))
        sources.append(str(domain.relative_to(args.repo)))
    if knowledge:
        rows.extend(harvest_ua_knowledge(knowledge))
        sources.append(str(knowledge.relative_to(args.repo)))
    if args.gitnexus_export:
        gitnexus_export = args.gitnexus_export
        rows.extend(harvest_gitnexus(gitnexus_export))
        sources.append(str(gitnexus_export))
    return rows, sources, gitnexus_export


def maybe_write_communities(repo: Path, export: Path | None) -> Path | None:
    if export is None:
        return None
    path = write_communities_summary(repo, export)
    print(f"Wrote compact communities summary {path}.")
    return path


def cmd_harvest(args: argparse.Namespace) -> int:
    try:
        rows, sources, gitnexus_export = collect_candidates(args)
    except ValueError as error:
        return fail(str(error), 2)
    if not rows:
        return fail(
            "no flow candidates found; provide UA graphs or --gitnexus-export "
            "from the GitNexus MCP",
            2,
        )
    maybe_write_communities(args.repo, gitnexus_export)
    rows = finalize(rows, args.main_limit, args.repo)
    target = write_index(args.repo, rows, sources)
    summary = summary_for(rows)
    print(
        f"Wrote {target} — {summary['total']} flow candidates "
        f"({summary['main']} main, {summary['deferred']} deferred)."
    )
    return 0


def cmd_revise(args: argparse.Namespace) -> int:
    try:
        rows, sources, gitnexus_export = collect_candidates(args)
    except ValueError as error:
        return fail(str(error), 2)
    if not rows:
        return fail(
            "no flow candidates found; provide UA graphs or --gitnexus-export "
            "from the GitNexus MCP",
            2,
        )
    communities_path = maybe_write_communities(args.repo, gitnexus_export)
    existing = load_existing_index(args.repo)
    prior = prior_by_key(existing)
    if existing and existing.get("sources"):
        for source in existing["sources"]:
            if source not in sources:
                sources.append(source)
    rows = finalize(rows, args.main_limit, args.repo)
    rows = apply_revise_statuses(rows, prior)
    stubs = ensure_stubs(args.repo, rows)
    pruned = prune_orphan_stubs(args.repo, rows)
    target = write_index(args.repo, rows, sources)
    summary = summary_for(rows)
    main_priority = [
        {
            "id": row["id"],
            "slug": row["slug"],
            "path": resolve_doc_path(row) or default_doc_path(row["slug"], row.get("family")),
            "name": row.get("display_name") or row["name"],
            "status": row["status"],
            "doc_role": row.get("doc_role"),
        }
        for row in rows
        if row.get("priority") == "main"
        and row["status"] != "skipped"
        and row.get("doc_role") == "standalone"
    ]
    documented = [row["id"] for row in rows if row["status"] == "documented"]
    print(
        f"Revised {target} — {summary['total']} flows "
        f"({summary['placeholder']} placeholder, {summary['documented']} documented, "
        f"{summary['main']} main-priority)."
    )
    print(f"Created/refreshed {len(stubs)} main-priority placeholder stub(s).")
    if pruned:
        print(f"Pruned {len(pruned)} orphan scaffold stub(s).")
    if main_priority:
        print("NOTICE: main-priority flows eligible for full documentation:")
        for item in main_priority:
            print(f"  - {item['name']} ({item['path']}) [{item['status']}]")
    report = {
        "index": str(target),
        "summary": summary,
        "stubs": stubs,
        "pruned": pruned,
        "main_priority": main_priority,
        "documented": documented,
        "update_existing": documented,
        "communities": str(communities_path) if communities_path else None,
    }
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


def build_organization_pack(index: dict) -> dict:
    flows = []
    for row in index.get("flows", []):
        if not isinstance(row, dict):
            continue
        entry = row.get("entry_ref") or {}
        flows.append({
            "id": row.get("id"),
            "name": row.get("name"),
            "display_name": row.get("display_name") or row.get("name"),
            "slug": row.get("slug"),
            "priority": row.get("priority"),
            "status": row.get("status"),
            "doc_role": row.get("doc_role"),
            "family": row.get("family"),
            "composed_into": row.get("composed_into"),
            "doc_path": row.get("doc_path"),
            "area": row.get("area"),
            "rank": row.get("rank"),
            "confidence": row.get("confidence"),
            "entry_ref": entry,
            "module_hint": module_from_path(entry.get("filePath")),
        })
    return {
        "version": "1.0",
        "generated_at": now_iso(),
        "project": index.get("project"),
        "rules": {
            "display_name": "Reader-recognizable business outcome, not a bare symbol.",
            "family": "Kebab folder/group key when ≥3 related documentable siblings.",
            "compose": (
                "Small related endpoint/service ops sharing a domain become "
                "doc_role=member with composed_into pointing at a standalone parent."
            ),
            "doc_path": "docs/flows/{family}/{slug}.md when family is set; else docs/flows/{slug}.md.",
            "doc_role": {
                "standalone": "Own deep-dive markdown (main budget).",
                "member": "Section inside parent; no stub file.",
                "index_only": "Index row only; typical for deferred.",
            },
        },
        "flows": flows,
    }


def cmd_organize_emit(args: argparse.Namespace) -> int:
    try:
        index = read_json(args.repo / INDEX_REL)
    except ValueError as error:
        return fail(str(error), 2)
    for row in index.get("flows", []):
        if isinstance(row, dict):
            apply_org_defaults(row)
    pack = build_organization_pack(index)
    from graph_storage import ensure_tmp_dir_gitignored

    ensure_tmp_dir_gitignored(args.repo)
    target = args.output or (args.repo / ORG_PACK_REL)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(pack, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote organization pack {target} — {len(pack['flows'])} flows.")
    print(
        "Next: agent writes .docforge/tmp/flow-organization.json, then "
        "flow_index organize apply --organization <path>."
    )
    return 0


def validate_organization(org: dict, by_id: dict[str, dict]) -> list[str]:
    errors: list[str] = []
    if org.get("version") != "1.0":
        errors.append("organization version must be 1.0")
    updates = org.get("updates")
    if not isinstance(updates, list) or not updates:
        errors.append("organization.updates must be a non-empty array")
        return errors
    seen_slugs: dict[str, str] = {}
    for row in by_id.values():
        if row.get("doc_role") != "member":
            seen_slugs[row["slug"]] = row["id"]
    for index, update in enumerate(updates):
        if not isinstance(update, dict):
            errors.append(f"updates[{index}] must be an object")
            continue
        flow_id = update.get("id")
        if not isinstance(flow_id, str) or flow_id not in by_id:
            errors.append(f"updates[{index}].id must reference an existing flow")
            continue
        if "slug" in update and update["slug"] is not None:
            slug = update["slug"]
            if not isinstance(slug, str) or not SLUG_RE.match(slug):
                errors.append(f"updates[{index}].slug is invalid")
            else:
                owner = seen_slugs.get(slug)
                if owner and owner != flow_id:
                    # Allow stealing slug from this update set by clearing later.
                    conflicting = next(
                        (
                            other for other in updates
                            if isinstance(other, dict)
                            and other.get("id") == owner
                            and other.get("slug") not in {None, slug}
                        ),
                        None,
                    )
                    if not conflicting and owner != flow_id:
                        # Check if owner is being renamed away in same batch.
                        owner_update = next(
                            (u for u in updates if isinstance(u, dict) and u.get("id") == owner),
                            None,
                        )
                        if not owner_update or owner_update.get("slug") in (None, slug):
                            if owner_update is None or "slug" not in owner_update:
                                errors.append(
                                    f"updates[{index}].slug '{slug}' already used by {owner}"
                                )
                seen_slugs[slug] = flow_id
        if "family" in update and update["family"] is not None:
            if not isinstance(update["family"], str) or not FAMILY_RE.match(update["family"]):
                errors.append(f"updates[{index}].family is invalid")
        if "doc_role" in update and update["doc_role"] not in {
            "standalone", "member", "index_only", None,
        }:
            errors.append(f"updates[{index}].doc_role is invalid")
        if "composed_into" in update and update["composed_into"] is not None:
            parent = update["composed_into"]
            if not isinstance(parent, str) or not FLOW_ID_RE.match(parent):
                errors.append(f"updates[{index}].composed_into is invalid")
            elif parent not in by_id and parent != flow_id:
                # Parent may be referenced; must exist in index.
                if parent not in by_id:
                    errors.append(f"updates[{index}].composed_into unknown: {parent}")
        members = update.get("compose_members")
        if members is not None:
            if not isinstance(members, list):
                errors.append(f"updates[{index}].compose_members must be an array")
            else:
                for member_id in members:
                    if member_id not in by_id:
                        errors.append(
                            f"updates[{index}].compose_members unknown id: {member_id}"
                        )
        if "doc_path" in update and update["doc_path"] is not None:
            path = update["doc_path"]
            if not isinstance(path, str) or not path.startswith("docs/flows/") or not path.endswith(".md"):
                errors.append(f"updates[{index}].doc_path must be under docs/flows/*.md")
    return errors


def move_or_write_stub(repo: Path, row: dict, previous_path: str | None) -> None:
    """Move filled docs or refresh stubs when doc_path changes."""
    new_path = resolve_doc_path(row)
    if previous_path and previous_path != new_path:
        old = repo / previous_path
        if old.is_file():
            text = old.read_text(encoding="utf-8")
            if new_path:
                target = repo / new_path
                target.parent.mkdir(parents=True, exist_ok=True)
                if not target.is_file():
                    target.write_text(text, encoding="utf-8")
                elif is_scaffold_or_placeholder(target.read_text(encoding="utf-8")) and not is_scaffold_or_placeholder(text):
                    target.write_text(text, encoding="utf-8")
            if is_scaffold_or_placeholder(text) or (new_path and (repo / new_path).is_file()):
                if old.is_file() and (not new_path or old.resolve() != (repo / new_path).resolve()):
                    old.unlink()
    if should_stub(row) and new_path:
        target = repo / new_path
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.is_file() or is_scaffold_or_placeholder(target.read_text(encoding="utf-8")):
            target.write_text(stub_body(row), encoding="utf-8")


def cmd_organize_apply(args: argparse.Namespace) -> int:
    try:
        index = read_json(args.repo / INDEX_REL)
        org = read_json(args.organization)
    except ValueError as error:
        return fail(str(error), 2)
    rows = [row for row in index.get("flows", []) if isinstance(row, dict)]
    for row in rows:
        apply_org_defaults(row)
    by_id = {row["id"]: row for row in rows}
    errors = validate_organization(org, by_id)
    if errors:
        for item in errors:
            print(f"error: {item}", file=sys.stderr)
        return 2

    previous_paths = {row["id"]: resolve_doc_path(row) for row in rows}

    for update in org["updates"]:
        row = by_id[update["id"]]
        if "display_name" in update and update["display_name"]:
            row["display_name"] = str(update["display_name"])
        if "slug" in update and update["slug"]:
            row["slug"] = str(update["slug"])
            # Keep durable id stable; only slug/path change for readers.
        if "family" in update:
            row["family"] = update["family"]
        if "doc_role" in update and update["doc_role"]:
            row["doc_role"] = update["doc_role"]
        if "composed_into" in update:
            row["composed_into"] = update["composed_into"]
        if "doc_path" in update:
            row["doc_path"] = update["doc_path"]
        members = update.get("compose_members") or []
        if members:
            row["doc_role"] = "standalone"
            if row.get("priority") != "main":
                row["priority"] = "main"
            if not row.get("doc_path"):
                row["doc_path"] = default_doc_path(row["slug"], row.get("family"))
            for member_id in members:
                member = by_id[member_id]
                member["doc_role"] = "member"
                member["composed_into"] = row["id"]
                member["family"] = row.get("family") or member.get("family")
                member["doc_path"] = None

    # Normalize paths/roles after updates.
    used_slugs: dict[str, str] = {}
    for row in rows:
        apply_org_defaults(row)
        if row.get("doc_role") == "member":
            row["doc_path"] = None
            continue
        if row.get("doc_role") == "index_only":
            row["doc_path"] = None
            continue
        if not row.get("doc_path"):
            row["doc_path"] = default_doc_path(row["slug"], row.get("family"))
        owner = used_slugs.get(row["slug"])
        if owner and owner != row["id"]:
            return fail(f"duplicate slug after apply: {row['slug']}", 2)
        used_slugs[row["slug"]] = row["id"]

    for row in rows:
        move_or_write_stub(repo=args.repo, row=row, previous_path=previous_paths.get(row["id"]))

    pruned = prune_orphan_stubs(args.repo, rows)
    index["version"] = INDEX_VERSION
    index["generated_at"] = now_iso()
    index["flows"] = rows
    index["summary"] = summary_for(rows)
    target = args.repo / INDEX_REL
    target.write_text(json.dumps(index, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Applied organization to {target} — {len(org['updates'])} update(s).")
    if pruned:
        print(f"Pruned {len(pruned)} orphan scaffold stub(s).")
    print(json.dumps({
        "index": str(target),
        "updates": len(org["updates"]),
        "pruned": pruned,
        "summary": index["summary"],
    }, indent=2, ensure_ascii=False))
    return 0


def cmd_render(args: argparse.Namespace) -> int:
    try:
        index = read_json(args.repo / INDEX_REL)
    except ValueError as error:
        return fail(str(error), 2)
    for row in index.get("flows", []):
        if isinstance(row, dict):
            apply_org_defaults(row)
    tier = "spine"
    manifest_path = args.repo / ".docforge/manifest.json"
    if manifest_path.is_file():
        try:
            tier = read_json(manifest_path).get("project", {}).get("tier", tier)
        except ValueError:
            pass
    target = args.output or args.repo / "docs/flows/README.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(markdown(index, tier, args.repo), encoding="utf-8")
    print(f"Rendered {target} — {len(index.get('flows', []))} indexed flows.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    def add_harvest_flags(command: argparse.ArgumentParser) -> None:
        command.add_argument("--repo", required=True, type=Path)
        command.add_argument("--gitnexus-export", type=Path)
        command.add_argument("--main-limit", type=int, default=15)

    harvest = sub.add_parser("harvest")
    add_harvest_flags(harvest)
    harvest.set_defaults(func=cmd_harvest)
    revise = sub.add_parser("revise")
    add_harvest_flags(revise)
    revise.set_defaults(func=cmd_revise)
    render = sub.add_parser("render")
    render.add_argument("--repo", required=True, type=Path)
    render.add_argument("--output", type=Path)
    render.set_defaults(func=cmd_render)

    organize = sub.add_parser("organize")
    organize_sub = organize.add_subparsers(dest="organize_command", required=True)
    emit = organize_sub.add_parser("emit")
    emit.add_argument("--repo", required=True, type=Path)
    emit.add_argument("--output", type=Path)
    emit.set_defaults(func=cmd_organize_emit)
    apply = organize_sub.add_parser("apply")
    apply.add_argument("--repo", required=True, type=Path)
    apply.add_argument("--organization", required=True, type=Path)
    apply.set_defaults(func=cmd_organize_apply)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if not args.repo.is_dir():
        return fail(f"not a directory: {args.repo}", 2)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
