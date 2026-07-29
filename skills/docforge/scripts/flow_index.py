#!/usr/bin/env python3
"""Harvest, rank, revise, and render Docforge's complete repository flow index.

Understand Anything JSON is read directly. GitNexus is consumed through a
small JSON export produced by its MCP/cypher interface, keeping this tool
standard-library-only and equivalent to its Node peer.

  python flow_index.py harvest --repo <repo> [--gitnexus-export <json>]
  python flow_index.py revise --repo <repo> [--gitnexus-export <json>]
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
UA_DIRS = (".ua", ".understand-anything")
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
    by_id = {node.get("id"): node for node in nodes}
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
    """Read an MCP export: {routes:[], processes:[], communities:[]}.

    Process entries are grouped by entryPointId. The export may contain raw
    Process properties or aliases returned by a cypher query.
    """
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
        labels = [communities[value] for value in community_ids if communities.get(value)]
        cross = any(item.get("processType") == "cross_community" or item.get("process_type") == "cross_community" for item in processes)
        name = str(symbol or processes[0].get("heuristicLabel") or entry_id)
        rows.append(candidate(
            name=name,
            kind=infer_kind(name, file_path),
            signature=entry_id,
            file_path=file_path,
            symbol=symbol,
            area=", ".join(sorted(labels)) or processes[0].get("communityLabel"),
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


def row_key(row: dict) -> str:
    entry = row["entry_ref"]
    if entry.get("filePath") and entry.get("symbol"):
        return f"{entry['filePath']}::{entry['symbol']}".lower()
    return f"{entry.get('kind')}::{entry.get('signature')}".lower()


def merge_rows(rows: list[dict]) -> list[dict]:
    merged: dict[str, dict] = {}
    for row in rows:
        key = row_key(row)
        if key not in merged:
            merged[key] = row
            continue
        current = merged[key]
        current["evidence"].extend(
            item for item in row["evidence"] if item not in current["evidence"]
        )
        if row["confidence"] == "confirmed":
            current["confidence"] = "confirmed"
            current["name"] = row["name"]
            current["entry_ref"] = row["entry_ref"]
        current["reach"]["steps"] = max(current["reach"]["steps"], row["reach"]["steps"])
        current["reach"]["boundaries"] = max(current["reach"]["boundaries"], row["reach"]["boundaries"])
        current["reach"]["churn"] = max(current["reach"].get("churn", 0), row["reach"].get("churn", 0))
        if current["area"] == "Unclassified" and row["area"] != "Unclassified":
            current["area"] = row["area"]
    return list(merged.values())


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


def finalize(rows: list[dict], main_limit: int, repo: Path | None = None) -> list[dict]:
    rows = merge_rows(rows)
    if repo is not None:
        add_churn(repo, rows)
    for row in rows:
        row["rank"] = score(row)
    rows.sort(key=lambda item: (-item["rank"], item["name"].lower(), row_key(item)))
    used: dict[str, int] = {}
    for index, row in enumerate(rows):
        base = slugify(row["name"])
        used[base] = used.get(base, 0) + 1
        slug = base if used[base] == 1 else f"{base}-{used[base]}"
        row["slug"] = slug
        row["id"] = f"flow-{slug}"
        priority = "main" if index < max(main_limit, 0) else "deferred"
        row["priority"] = priority
        row["status"] = priority
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
    """Preserve documented/skipped; mark everything else placeholder; keep stable ids."""
    for row in rows:
        previous = prior.get(row_key(row))
        if previous is None:
            row["status"] = "placeholder"
            continue
        prior_status = previous.get("status")
        if prior_status in {"documented", "skipped"}:
            row["status"] = prior_status
            # Keep durable path identity for existing docs/stubs.
            if previous.get("slug"):
                row["slug"] = previous["slug"]
                row["id"] = previous.get("id") or f"flow-{previous['slug']}"
            if previous.get("priority") in {"main", "deferred"}:
                row["priority"] = previous["priority"]
        else:
            row["status"] = "placeholder"
            if previous.get("slug") and (previous.get("status") in {"placeholder", "main", "deferred"}):
                # Prefer prior slug when a stub already exists under that name.
                row["slug"] = previous["slug"]
                row["id"] = previous.get("id") or f"flow-{previous['slug']}"
    return rows


def row_priority(row: dict) -> str | None:
    if row.get("priority") in {"main", "deferred"}:
        return row["priority"]
    if row["status"] in {"main", "deferred"}:
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
    providers = sorted({e["provider"] for row in rows for e in row["evidence"]})
    value = {
        "version": "1.0",
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


def stub_body(row: dict) -> str:
    name = row["name"]
    slug = row["slug"]
    entry = row["entry_ref"]
    signature = entry.get("signature") or name
    provenance = scaffold_provenance(
        row["id"],
        f"docs/flows/{slug}.md",
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


def ensure_stubs(repo: Path, rows: list[dict]) -> list[dict]:
    """Create stub markdown for placeholder rows; never overwrite filled docs."""
    created: list[dict] = []
    flows_dir = repo / "docs" / "flows"
    flows_dir.mkdir(parents=True, exist_ok=True)
    for row in rows:
        if row["status"] != "placeholder":
            continue
        target = flows_dir / f"{row['slug']}.md"
        if target.is_file():
            existing = target.read_text(encoding="utf-8")
            if not is_scaffold_or_placeholder(existing):
                continue
        target.write_text(stub_body(row), encoding="utf-8")
        created.append({
            "id": row["id"],
            "slug": row["slug"],
            "path": f"docs/flows/{row['slug']}.md",
            "priority": row.get("priority", "deferred"),
            "name": row["name"],
        })
    return created


def flow_doc_exists(repo: Path | None, slug: str) -> bool:
    if repo is None:
        return False
    return (repo / "docs" / "flows" / f"{slug}.md").is_file()


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
        "rows get deep-dive documentation; `placeholder` rows have stub files;",
        "`deferred` priority rows remain discoverable.",
        "",
        "| Status | Flow | Trigger | Entry point | Area | Confidence | Reach |",
        "|---|---|---|---|---|---|---|",
    ]
    for row in index.get("flows", []):
        entry = row["entry_ref"]
        name = row["name"].replace("|", "\\|")
        if row["status"] in {"documented", "placeholder"} and flow_doc_exists(repo, row["slug"]):
            name = f"[{name}](./{row['slug']}.md)"
        elif row["status"] == "documented":
            name = f"[{name}](./{row['slug']}.md)"
        signature = str(entry.get("signature") or "").replace("|", "\\|")
        area = str(row.get("area") or "").replace("|", "\\|")
        reach = (
            f"{row['reach']['steps']} steps / {row['reach']['boundaries']} boundaries / "
            f"{row['reach'].get('churn', 0)} changes"
        )
        lines.append(
            f"| {row['status']} | {name} | {entry['kind']} | `{signature}` | "
            f"{area} | {row['confidence']} | {reach} |"
        )
    lines += [
        "",
        f"_Generated {generated}; source of truth: `.docforge/flow-index.json`._",
        "",
    ]
    return emit_yaml(provenance) + "\n".join(lines)


def collect_candidates(args: argparse.Namespace) -> tuple[list[dict], list[str]]:
    rows: list[dict] = []
    sources: list[str] = []
    domain = find_ua(args.repo, "domain-graph.json")
    knowledge = find_ua(args.repo, "knowledge-graph.json")
    if domain:
        rows.extend(harvest_ua_domain(domain))
        sources.append(str(domain.relative_to(args.repo)))
    if knowledge:
        rows.extend(harvest_ua_knowledge(knowledge))
        sources.append(str(knowledge.relative_to(args.repo)))
    if args.gitnexus_export:
        rows.extend(harvest_gitnexus(args.gitnexus_export))
        sources.append(str(args.gitnexus_export))
    return rows, sources


def cmd_harvest(args: argparse.Namespace) -> int:
    try:
        rows, sources = collect_candidates(args)
    except ValueError as error:
        return fail(str(error), 2)
    if not rows:
        return fail(
            "no flow candidates found; provide UA graphs or --gitnexus-export "
            "from the GitNexus MCP",
            2,
        )
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
        rows, sources = collect_candidates(args)
    except ValueError as error:
        return fail(str(error), 2)
    if not rows:
        return fail(
            "no flow candidates found; provide UA graphs or --gitnexus-export "
            "from the GitNexus MCP",
            2,
        )
    existing = load_existing_index(args.repo)
    prior = prior_by_key(existing)
    if existing and existing.get("sources"):
        for source in existing["sources"]:
            if source not in sources:
                sources.append(source)
    rows = finalize(rows, args.main_limit, args.repo)
    rows = apply_revise_statuses(rows, prior)
    stubs = ensure_stubs(args.repo, rows)
    target = write_index(args.repo, rows, sources)
    summary = summary_for(rows)
    main_priority = [
        {
            "id": row["id"],
            "slug": row["slug"],
            "path": f"docs/flows/{row['slug']}.md",
            "name": row["name"],
            "status": row["status"],
        }
        for row in rows
        if row.get("priority") == "main" and row["status"] != "skipped"
    ]
    documented = [row["id"] for row in rows if row["status"] == "documented"]
    print(
        f"Revised {target} — {summary['total']} flows "
        f"({summary['placeholder']} placeholder, {summary['documented']} documented, "
        f"{summary['main']} main-priority)."
    )
    print(f"Created/refreshed {len(stubs)} placeholder stub(s).")
    if main_priority:
        print("NOTICE: main-priority flows eligible for full documentation:")
        for item in main_priority:
            print(f"  - {item['name']} ({item['path']}) [{item['status']}]")
    report = {
        "index": str(target),
        "summary": summary,
        "stubs": stubs,
        "main_priority": main_priority,
        "documented": documented,
        "update_existing": documented,
    }
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


def cmd_render(args: argparse.Namespace) -> int:
    try:
        index = read_json(args.repo / INDEX_REL)
    except ValueError as error:
        return fail(str(error), 2)
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
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if not args.repo.is_dir():
        return fail(f"not a directory: {args.repo}", 2)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
