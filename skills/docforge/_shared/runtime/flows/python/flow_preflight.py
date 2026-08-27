#!/usr/bin/env python3
"""Surface-aware structural preflight for flow investigation.

The flow index deliberately stays a compact document catalog.  This command
keeps the larger, lossless structural record it is selected from at
``.docforge/flow-evidence.json``.  The record is provider-neutral: native
GitNexus processes and CodeGraph call paths are represented as independent
path variants over one topology, rather than being collapsed into prose or a
single "best" chain.

    python flow_preflight.py prepare --repo <repo>
    python flow_preflight.py import --repo <repo> --input <enrichment.json>
    python flow_preflight.py status --repo <repo> [--json]
    python flow_preflight.py validate --repo <repo>

``import`` is intentionally additive.  It is the hand-off for MCP/source
reads that resolve a graph gap; a refresh preserves that enrichment only when
the affected entry fingerprint has not changed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sqlite3
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from runtime.common.python._util import dump_json, fail, load_manifest

EVIDENCE_REL = Path(".docforge/flow-evidence.json")
SCHEMA_VERSION = "1.0"
SURFACE_KINDS = {
    "request", "event", "schedule", "ui", "command", "library",
    "lifecycle", "operation", "internal",
}
SUBTYPE_TO_KIND = {
    "http": "request", "graphql": "request", "grpc": "request", "webhook": "request",
    "queue": "event", "pubsub": "event", "listener": "event",
    "cron": "schedule", "timer": "schedule", "batch": "schedule",
    "screen-route": "ui", "desktop-action": "ui",
    "cli": "command", "tui": "command",
    "public-api": "library",
    "start": "lifecycle", "background": "lifecycle", "shutdown": "lifecycle",
    "migration": "operation", "deployment": "operation", "infrastructure-apply": "operation",
    "unresolved": "internal",
}
REQUIRED_GAPS = {"missing-ordering", "missing-locator", "missing-terminal", "unknown-terminal", "incomplete-topology", "unresolved-service-dispatch", "semantic-investigation"}
MAX_CODEGRAPH_SEEDS = 120


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def path_for(repo: Path) -> Path:
    return repo / EVIDENCE_REL


def stable_id(prefix: str, *parts: object) -> str:
    text = "|".join(str(part or "") for part in parts)
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]
    return f"{prefix}-{digest}"


def fingerprint(path: Path, repo: Path | None = None) -> dict | None:
    if not path.is_file():
        return None
    try:
        raw = path.read_bytes()
        rel = path.relative_to(repo).as_posix() if repo else str(path)
    except (OSError, ValueError):
        return None
    return {"path": rel, "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}


def source_fingerprint(repo: Path, provider: str) -> dict | None:
    choices = {
        "codegraph": repo / ".codegraph" / "codegraph.db",
        "gitnexus": repo / ".docforge" / "tmp" / "gitnexus-flows.json",
    }
    return fingerprint(choices.get(provider, Path("/missing")), repo)


def locked_provider(repo: Path) -> str | None:
    manifest = repo / ".docforge" / "manifest.json"
    if not manifest.is_file():
        return None
    try:
        record = load_manifest(manifest)
    except ValueError:
        return None
    graph = record.get("graph")
    return str(graph.get("provider")) if isinstance(graph, dict) and graph.get("provider") else None


def detect_provider(repo: Path) -> str:
    locked = locked_provider(repo)
    if locked in {"codegraph", "gitnexus"}:
        return locked
    if (repo / ".docforge" / "tmp" / "gitnexus-flows.json").is_file():
        return "gitnexus"
    if (repo / ".codegraph" / "codegraph.db").is_file():
        return "codegraph"
    return "unknown"


def project_facts(repo: Path) -> dict:
    """Reuse confirmed profiles and the architecture ledger when they exist.

    A manifest records a user-confirmed selection.  Detection supplements it
    instead of overwriting it, so a multi-label project remains multi-label.
    """
    profiles = {"shapes": [], "frameworks": []}
    profile_evidence: list[dict] = []
    manifest_path = repo / ".docforge" / "manifest.json"
    if manifest_path.is_file():
        try:
            manifest = load_manifest(manifest_path)
            selected = manifest.get("project", {}).get("profiles", {})
            for key in profiles:
                values = selected.get(key, []) if isinstance(selected, dict) else []
                profiles[key].extend(str(value) for value in values if value)
                for value in values:
                    profile_evidence.append({
                        "id": stable_id("evidence", "manifest", key, value),
                        "provider": "manifest", "kind": "confirmed-profile",
                        "value": str(value), "artifact": ".docforge/manifest.json",
                    })
        except ValueError:
            pass
    try:
        from runtime.catalog.python.detect_profiles import detect
        for item in detect(repo, persist=False):
            if item.get("dimension") not in profiles:
                continue
            value = str(item.get("id") or "")
            if not value:
                continue
            profiles[item["dimension"]].append(value)
            profile_evidence.append({
                "id": stable_id("evidence", "detect-profiles", item["dimension"], value),
                "provider": "detect_profiles", "kind": "profile",
                "value": value, "confidence": item.get("confidence"),
                "artifact": ",".join(item.get("evidence") or []),
            })
    except (ImportError, OSError, ValueError):
        pass
    for key in profiles:
        profiles[key] = sorted(set(profiles[key]))

    blocks: list[dict] = []
    relationships: list[dict] = []
    architecture = repo / ".docforge" / "architecture-plan.json"
    if architecture.is_file():
        try:
            plan = json.loads(architecture.read_text(encoding="utf-8"))
            system = plan.get("system", {}) if isinstance(plan, dict) else {}
            blocks = [item for item in system.get("deployable_blocks", []) if isinstance(item, dict)]
            relationships = [item for item in system.get("relationships", []) if isinstance(item, dict)]
        except (OSError, json.JSONDecodeError):
            pass
    # The architecture ledger is preferred, but a preflight also needs to see
    # deployable boundaries before that ledger has been authored.
    deployment_patterns = {"Dockerfile": "container", "docker-compose.yml": "compose",
                           "compose.yml": "compose", "compose.yaml": "compose"}
    known_paths = {str(item.get("path") or "") for item in blocks}
    try:
        from runtime.catalog.python.detect_profiles import inventory
        deployment_files = inventory(repo)
    except (ImportError, OSError):
        deployment_files = []
    for rel, _ in deployment_files:
        block_kind = deployment_patterns.get(Path(rel).name)
        if Path(rel).suffix == ".tf":
            block_kind = "infrastructure-apply"
        if block_kind and rel not in known_paths:
            blocks.append({"id": stable_id("deployable", rel), "kind": block_kind, "path": rel, "inferred": True})
            known_paths.add(rel)
    return {
        "shapes": profiles["shapes"],
        "frameworks": profiles["frameworks"],
        "deployable_blocks": sorted(blocks, key=lambda item: str(item.get("id") or "")),
        "external_relationships": sorted(relationships, key=lambda item: (
            str(item.get("origin") or ""), str(item.get("destination") or ""),
        )),
        "profile_evidence": sorted(profile_evidence, key=lambda item: item["id"]),
    }


def classify(signature: str, path: str | None = None, raw_kind: str | None = None) -> tuple[str, str]:
    text = f"{signature} {path or ''} {raw_kind or ''}".lower()
    if raw_kind == "route" or re.search(r"\b(get|post|put|patch|delete)\b|/api/|route", text):
        return "request", "http"
    if "graphql" in text:
        return "request", "graphql"
    if "grpc" in text:
        return "request", "grpc"
    if "webhook" in text:
        return "request", "webhook"
    if re.search(r"queue|consumer|message", text):
        return "event", "queue"
    if re.search(r"pub.?sub", text):
        return "event", "pubsub"
    if "listener" in text:
        return "event", "listener"
    if "cron" in text:
        return "schedule", "cron"
    if re.search(r"schedule|timer|job|batch", text):
        return "schedule", "batch"
    if re.search(r"command|cli", text):
        return "command", "cli"
    if re.search(r"screen|view|component|page|window", text):
        return "ui", "screen-route"
    if re.search(r"main|startup|boot|application", text):
        return "lifecycle", "start"
    if re.search(r"migrat", text):
        return "operation", "migration"
    if re.search(r"terraform|pulumi|deploy|apply", text):
        return "operation", "infrastructure-apply"
    if raw_kind in {"function", "method"} and re.search(r"export|public", text):
        return "library", "public-api"
    return "internal", "unresolved"


def locator(node_id: object, symbol: object, file_path: object, line: object = None) -> dict:
    value = {"node_id": str(node_id) if node_id is not None else None,
             "symbol": str(symbol) if symbol is not None else None,
             "file_path": str(file_path) if file_path is not None else None}
    if isinstance(line, int):
        value["line"] = line
    return value


def surface_scope(file_path: object) -> str:
    """A runtime surface is broader than one route/function.

    Group siblings under the same source directory so ten HTTP routes in the
    same API adapter reserve one coverage slot, rather than exhausting the
    budget before a confirmed timer or CLI gets a turn.
    """
    value = str(file_path or "").replace("\\", "/").strip("/")
    return value.rsplit("/", 1)[0] if "/" in value else (value or "repository")


def node_record(node_id: str, label: str | None, loc: dict, provider: str, kind: str = "code") -> dict:
    return {"id": node_id, "label": label or node_id, "kind": kind,
            "locator": loc, "provider_ids": [provider]}


def graph_entry_fingerprint(repo: Path, item: dict) -> list[dict]:
    result = []
    path = item.get("path")
    if path:
        digest = fingerprint(repo / str(path), repo)
        if digest:
            result.append(digest)
    if not result:
        raw = json.dumps({key: item.get(key) for key in ("id", "name", "path", "line", "rank")}, sort_keys=True)
        result.append({"path": f".codegraph/codegraph.db#entry:{item.get('id')}",
                       "sha256": hashlib.sha256(raw.encode("utf-8")).hexdigest(), "bytes": len(raw)})
    return result


def build_codegraph(repo: Path) -> tuple[list[dict], list[dict], list[dict], list[dict], list[dict], list[dict]]:
    """Return entries, nodes, edges, variants, terminals, gaps.

    ``ordered_paths`` supplies every retained path.  Prefix nodes are shared by
    their stable CodeGraph node id, making a DAG even on old CodeGraph indexes
    whose reader cannot expose a richer control-flow graph.
    """
    try:
        from runtime.graph.python.graph_source_codegraph_reader import entry_points, ordered_paths
    except ImportError:
        return [], [], [], [], [], []
    entries: list[dict] = []; nodes: dict[str, dict] = {}; edges: dict[str, dict] = {}
    variants: list[dict] = []; terminals: dict[str, dict] = {}; gaps: list[dict] = []
    for seed in entry_points(repo, MAX_CODEGRAPH_SEEDS):
        signature = str(seed.get("name") or seed.get("id"))
        kind, subtype = classify(signature, seed.get("path"), seed.get("kind"))
        entry_id = stable_id("entry", "codegraph", seed.get("id"))
        surface_id = stable_id("surface", kind, subtype, surface_scope(seed.get("path")))
        root_id = f"codegraph:{seed.get('id')}"
        root_loc = locator(seed.get("id"), seed.get("name"), seed.get("path"), seed.get("line"))
        nodes[root_id] = node_record(root_id, seed.get("name"), root_loc, "codegraph", "entry")
        evidence_id = stable_id("evidence", "codegraph", seed.get("id"))
        entry_gaps: list[str] = []
        paths = ordered_paths(repo, str(seed.get("id")))
        if not root_loc.get("file_path"):
            entry_gaps.append("missing-locator")
        if not paths:
            entry_gaps.append("missing-terminal")
        if len(paths) >= 12:
            gaps.append(gap(entry_id, "fanout-truncation", "CodeGraph retained-path cap was reached; additional branches may exist.", False))
        for path_index, chain in enumerate(paths, start=1):
            ordered = [root_id]
            previous = root_id
            for hop in chain:
                raw_node = str(hop.get("nodeId"))
                current = f"codegraph:{raw_node}"
                ordered.append(current)
                nodes.setdefault(current, node_record(
                    current, hop.get("symbol"),
                    locator(raw_node, hop.get("symbol"), hop.get("file"), hop.get("line")),
                    "codegraph", str(hop.get("kind") or "code"),
                ))
                edge_id = stable_id("edge", "codegraph", previous, current)
                edges.setdefault(edge_id, {"id": edge_id, "from": previous, "to": current,
                                            "type": str(hop.get("edgeType") or "calls"),
                                            "provider_ids": ["codegraph"]})
                previous = current
            terminal_id = stable_id("terminal", "codegraph", entry_id, path_index, previous)
            terminals[terminal_id] = {"id": terminal_id, "node_ref": previous,
                                      "entry_ref": entry_id, "outcome": "unknown"}
            variant_id = stable_id("path", "codegraph", entry_id, path_index,
                                   ">".join(ordered))
            variants.append({"id": variant_id, "entry_ref": entry_id,
                             "provider_ids": ["codegraph"], "ordered_nodes": ordered,
                             "terminal_ref": terminal_id, "process_id": None,
                             "type": "structural", "communities": [],
                             "truncated": bool(chain and chain[-1].get("order", 0) >= 6) or len(paths) >= 12})
            if chain and chain[-1].get("order", 0) >= 6:
                entry_gaps.append("missing-terminal")
                gaps.append(gap(entry_id, "depth-truncation", "CodeGraph call walk reached its depth cap.", False))
            if chain and str(chain[-1].get("kind") or "") in {"constant", "variable", "property"}:
                entry_gaps.append("unresolved-service-dispatch")
        if paths:
            # A graph leaf is a structural stop, not evidence of the business
            # terminal. Source/MCP investigation resolves this before a card
            # can be declared ready.
            entry_gaps.append("unknown-terminal")
            entry_gaps.append("unknown-condition")
        for position, issue in enumerate(sorted(set(entry_gaps)), start=1):
            gaps.append(gap(entry_id, issue, {
                "missing-locator": "Entry point has no source locator.",
                "missing-terminal": "No verified terminal is available from structural traversal.",
                "unknown-terminal": "CodeGraph leaf is structural; terminal outcome is not yet verified.",
                "unresolved-service-dispatch": "Structural walk ends at a service object; runtime dispatch is unresolved.",
                "unknown-condition": "CodeGraph call topology does not establish branch conditions.",
            }[issue], issue in REQUIRED_GAPS))
        entries.append({
            "id": entry_id, "name": signature, "surface_ref": surface_id,
            "trigger": {"kind": kind, "subtype": subtype, "signature": signature},
            "locator": root_loc, "provider_ids": ["codegraph"], "evidence_refs": [evidence_id],
            "graph_root_refs": [root_id], "topology_refs": [variant["id"] for variant in variants if variant["entry_ref"] == entry_id],
            "source_fingerprints": graph_entry_fingerprint(repo, seed),
            "analysis_state": "not-analyzed", "analysis_ready": not any(item in REQUIRED_GAPS for item in entry_gaps),
            "stale": False,
        })
    return entries, list(nodes.values()), list(edges.values()), variants, list(terminals.values()), gaps


def gap(entry_id: str | None, kind: str, message: str, required: bool = True) -> dict:
    return {"id": stable_id("gap", entry_id, kind, message), "entry_ref": entry_id,
            "type": kind, "message": message, "required": required, "provider_ids": []}


def split_symbol_id(value: object) -> tuple[str | None, str | None]:
    parts = str(value or "").split(":")
    return (parts[1] if len(parts) >= 3 else None, parts[-1] if parts else None)


def route_matches(route: dict, entry_id: object, symbol: str | None) -> bool:
    values = {str(route.get(key) or "") for key in ("id", "symbol", "name", "path", "route")}
    return str(entry_id) in values or bool(symbol and symbol in values)


def build_gitnexus(repo: Path) -> tuple[list[dict], list[dict], list[dict], list[dict], list[dict], list[dict]]:
    interchange = repo / ".docforge" / "tmp" / "gitnexus-flows.json"
    if not interchange.is_file():
        return [], [], [], [], [], []
    try:
        doc = json.loads(interchange.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return [], [], [], [], [], []
    routes = [row for row in doc.get("routes", []) if isinstance(row, dict)]
    processes = [row for row in doc.get("processes", []) if isinstance(row, dict)]
    communities = {str(row.get("id")): str(row.get("heuristicLabel") or row.get("name") or row.get("id"))
                   for row in doc.get("communities", []) if isinstance(row, dict)}
    nodes: dict[str, dict] = {}; edges: dict[str, dict] = {}; variants: list[dict] = []
    terminals: dict[str, dict] = {}; gaps: list[dict] = []; entries: list[dict] = []
    grouped: dict[str, list[dict]] = {}
    for process in processes:
        target = process.get("entryPointId") or process.get("entry_point_id")
        if target:
            grouped.setdefault(str(target), []).append(process)
    matched_routes: set[str] = set()
    for source_id, group in sorted(grouped.items()):
        file_path, symbol = split_symbol_id(source_id)
        matching = [route for route in routes if route_matches(route, source_id, symbol)]
        for route in matching:
            matched_routes.add(str(route.get("id") or route.get("path") or route.get("symbol")))
        signature = str((matching[0].get("path") if matching else None) or symbol or source_id)
        kind, subtype = classify(signature, file_path)
        entry_id = stable_id("entry", "gitnexus", source_id)
        surface_id = stable_id("surface", kind, subtype, surface_scope(file_path))
        root_id = f"gitnexus:{source_id}"
        root_loc = locator(source_id, symbol, file_path)
        nodes[root_id] = node_record(root_id, symbol or signature, root_loc, "gitnexus", "entry")
        entry_gaps: list[str] = []
        if not root_loc.get("file_path"):
            entry_gaps.append("missing-locator")
        if not matching and any(route_matches(route, source_id, symbol) for route in routes):
            entry_gaps.append("incomplete-topology")
        for process in sorted(group, key=lambda item: str(item.get("id") or "")):
            process_id = str(process.get("id") or stable_id("process", source_id, len(variants)))
            ordered = [root_id]; previous = root_id
            steps = process.get("steps") if isinstance(process.get("steps"), list) else []
            if not steps:
                entry_gaps.append("missing-ordering")
            for step in sorted((item for item in steps if isinstance(item, dict)), key=lambda item: (
                item.get("order") if isinstance(item.get("order"), int) else 0, str(item.get("nodeId") or item.get("node_id") or ""),
            )):
                node_value = step.get("nodeId") or step.get("node_id")
                current = f"gitnexus:{node_value or stable_id('step', process_id, len(ordered))}"
                ordered.append(current)
                nodes.setdefault(current, node_record(current, step.get("symbol") or step.get("name"), locator(
                    node_value, step.get("symbol") or step.get("name"), step.get("filePath") or step.get("file_path"), step.get("line")), "gitnexus"))
                edge_id = stable_id("edge", "gitnexus", process_id, previous, current)
                edges.setdefault(edge_id, {"id": edge_id, "from": previous, "to": current,
                                            "type": "step-in-process", "provider_ids": ["gitnexus"]})
                previous = current
            terminal_value = process.get("terminalId") or process.get("terminal_id")
            if not terminal_value:
                entry_gaps.append("missing-terminal")
            terminal_node = f"gitnexus:{terminal_value}" if terminal_value else previous
            if terminal_value and terminal_node not in nodes:
                term_path, term_symbol = split_symbol_id(terminal_value)
                nodes[terminal_node] = node_record(terminal_node, term_symbol, locator(terminal_value, term_symbol, term_path), "gitnexus", "terminal")
                edge_id = stable_id("edge", "gitnexus", process_id, previous, terminal_node)
                edges[edge_id] = {"id": edge_id, "from": previous, "to": terminal_node,
                                  "type": "terminal", "provider_ids": ["gitnexus"]}
                ordered.append(terminal_node)
            terminal_id = stable_id("terminal", "gitnexus", process_id, terminal_node)
            terminals[terminal_id] = {"id": terminal_id, "node_ref": terminal_node,
                                      "entry_ref": entry_id, "outcome": "unknown"}
            variant_id = stable_id("path", "gitnexus", process_id)
            declared_count = process.get("stepCount") or process.get("step_count")
            step_count = int(declared_count) if isinstance(declared_count, int) else len(steps)
            variants.append({"id": variant_id, "entry_ref": entry_id, "provider_ids": ["gitnexus"],
                             "ordered_nodes": ordered, "terminal_ref": terminal_id,
                             "process_id": process_id, "type": process.get("processType") or process.get("process_type") or "native-process",
                             "communities": sorted(communities.get(str(value), str(value)) for value in (process.get("communities") or [])),
                             "step_count": step_count,
                             "truncated": False})
        for issue in sorted(set(entry_gaps)):
            gaps.append(gap(entry_id, issue, {
                "missing-locator": "Entry point has no source locator.",
                "missing-ordering": "GitNexus process has no ordered STEP_IN_PROCESS evidence.",
                "missing-terminal": "GitNexus process has no terminal.",
                "incomplete-topology": "Route could not be matched to a process entry point.",
            }[issue], issue in REQUIRED_GAPS))
        # Native Process order is valuable structural evidence, but it cannot
        # establish guards, state effects, or business outcomes on its own.
        gaps.append(gap(entry_id, "semantic-investigation", "GitNexus native process proves ordering, not business meaning or analysis readiness.", True))
        entries.append({
            "id": entry_id, "name": signature, "surface_ref": surface_id,
            "trigger": {"kind": kind, "subtype": subtype, "signature": signature,
                        "routes": sorted(str(item.get("path") or item.get("route") or item.get("id")) for item in matching)},
            "locator": root_loc, "provider_ids": ["gitnexus"],
            "evidence_refs": [stable_id("evidence", "gitnexus", source_id), *[stable_id("evidence", "gitnexus", item.get("id")) for item in group]],
            "graph_root_refs": [root_id], "topology_refs": [item["id"] for item in variants if item["entry_ref"] == entry_id],
            "source_fingerprints": entry_fingerprints(repo, "gitnexus", source_id, group, file_path),
            "analysis_state": "not-analyzed", "analysis_ready": False, "stale": False,
        })
    # A Route without a matching Process is still a selectable request surface,
    # but it cannot become analysis-ready until a structural path is supplied.
    for route in routes:
        marker = str(route.get("id") or route.get("path") or route.get("symbol"))
        if marker in matched_routes:
            continue
        signature = str(route.get("path") or route.get("route") or route.get("name") or marker)
        entry_id = stable_id("entry", "gitnexus-route", marker)
        surface_id = stable_id("surface", "request", "http", surface_scope(route.get("filePath")))
        root_id = f"gitnexus:route:{marker}"
        loc = locator(route.get("id"), route.get("symbol") or route.get("name"), route.get("filePath"))
        nodes[root_id] = node_record(root_id, route.get("symbol") or signature, loc, "gitnexus", "route")
        route_gaps = ["incomplete-topology"] + (["missing-locator"] if not loc.get("file_path") else [])
        gaps.extend(gap(entry_id, value, "Route is not matched to a GitNexus Process." if value == "incomplete-topology" else "Route has no source locator.") for value in route_gaps)
        entries.append({"id": entry_id, "name": str(route.get("name") or signature), "surface_ref": surface_id,
                        "trigger": {"kind": "request", "subtype": "http", "signature": signature},
                        "locator": loc, "provider_ids": ["gitnexus"],
                        "evidence_refs": [stable_id("evidence", "gitnexus-route", marker)], "graph_root_refs": [root_id], "topology_refs": [],
                        "source_fingerprints": entry_fingerprints(repo, "gitnexus", marker, [route], route.get("filePath")),
                        "analysis_state": "not-analyzed", "analysis_ready": False, "stale": False})
    return entries, list(nodes.values()), list(edges.values()), variants, list(terminals.values()), gaps


def entry_fingerprints(repo: Path, provider: str, entry_id: object, records: list[dict], file_path: object) -> list[dict]:
    """Fingerprint the evidence for one entry, not the entire provider dump.

    The top-level provider fingerprint records index freshness.  Per-entry
    fingerprints are deliberately narrow so a changed nightly job does not
    discard an investigator's source enrichment for an unrelated API route.
    """
    result: list[dict] = []
    if file_path:
        digest = fingerprint(repo / str(file_path), repo)
        if digest:
            result.append(digest)
    raw = json.dumps(records, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    result.append({"path": f".docforge/tmp/{provider}-flows.json#entry:{entry_id}",
                   "sha256": hashlib.sha256(raw.encode("utf-8")).hexdigest(), "bytes": len(raw)})
    return result


def surfaces_for(entries: list[dict], facts: dict) -> list[dict]:
    by_id: dict[str, dict] = {}
    for entry in entries:
        surface_id = entry["surface_ref"]
        trigger = entry["trigger"]
        current = by_id.setdefault(surface_id, {
            "id": surface_id, "kind": trigger["kind"], "subtype": trigger["subtype"],
            "confidence": "confirmed" if trigger["kind"] != "internal" else "candidate",
            "evidence_refs": [], "evidence_gaps": [], "entry_refs": [], "graph_root_refs": [],
            "framework_registrations": [], "deployable_block_refs": [], "external_relationships": [],
        })
        current["evidence_refs"].extend(entry["evidence_refs"])
        current["entry_refs"].append(entry["id"])
        current["graph_root_refs"].extend(entry["graph_root_refs"])
    for item in by_id.values():
        item["evidence_refs"] = sorted(set(item["evidence_refs"]))
        item["entry_refs"] = sorted(set(item["entry_refs"]))
        item["graph_root_refs"] = sorted(set(item["graph_root_refs"]))
        item["framework_registrations"] = list(facts["frameworks"])
        item["deployable_block_refs"] = [str(block.get("id")) for block in facts["deployable_blocks"] if block.get("id")]
        item["external_relationships"] = list(facts["external_relationships"])
    return sorted(by_id.values(), key=lambda item: item["id"])


def derived_edges(variants: list[dict], topology_edges: list[dict]) -> tuple[list[str], list[str], list[dict]]:
    """Detect real divergence/rejoin in the retained prefix DAG.

    Cycle markers come from a repeated node in a variant.  The currently
    bounded offline CodeGraph reader cuts a cycle before it repeats, so a
    cycle-free result never claims there was no cycle — it simply has no marker.
    """
    outgoing: dict[str, set[str]] = {}; incoming: dict[str, set[str]] = {}
    cycle_edges: list[dict] = []
    for variant in variants:
        seen: set[str] = set()
        nodes = variant.get("ordered_nodes", [])
        for left, right in zip(nodes, nodes[1:]):
            outgoing.setdefault(left, set()).add(right)
            incoming.setdefault(right, set()).add(left)
            if right in seen:
                cycle_edges.append({"from": left, "to": right, "path_ref": variant["id"]})
            seen.add(left)
    by_pair: dict[tuple[str, str], list[str]] = {}
    for edge in topology_edges:
        by_pair.setdefault((str(edge.get("from")), str(edge.get("to"))), []).append(str(edge.get("id")))
    divergence = sorted(edge_id for node, children in outgoing.items() if len(children) > 1
                        for child in children for edge_id in by_pair.get((node, child), []))
    rejoin = sorted(edge_id for node, parents in incoming.items() if len(parents) > 1
                    for parent in parents for edge_id in by_pair.get((parent, node), []))
    return divergence, rejoin, sorted(cycle_edges, key=lambda item: (item["from"], item["to"], item["path_ref"]))


def codegraph_cycle_edges(repo: Path, node_ids: set[str]) -> list[dict]:
    """Mark visible recursive edges without expanding a cycle into a path."""
    db = repo / ".codegraph" / "codegraph.db"
    if not db.is_file():
        return []
    try:
        connection = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
        rows = connection.execute(
            "SELECT a.source AS source, a.target AS target FROM edges a "
            "JOIN edges b ON b.source = a.target AND b.target = a.source "
            "WHERE a.kind IN ('calls', 'references') AND b.kind IN ('calls', 'references')"
        ).fetchall()
        connection.close()
    except sqlite3.Error:
        return []
    result = []
    for source, target in rows:
        left, right = f"codegraph:{source}", f"codegraph:{target}"
        if left in node_ids and right in node_ids:
            result.append({"from": left, "to": right, "provider_ids": ["codegraph"], "type": "cycle"})
    return sorted({(item["from"], item["to"]): item for item in result}.values(), key=lambda item: (item["from"], item["to"]))


def evidence_records(provider: str, entries: list[dict], facts: dict) -> list[dict]:
    records = list(facts["profile_evidence"])
    for entry in entries:
        for evidence_id in entry.get("evidence_refs", []):
            records.append({"id": evidence_id, "provider": provider, "kind": "entry-topology",
                            "artifact": source_fingerprint_path(entry.get("source_fingerprints")),
                            "entry_ref": entry["id"], "locator": entry.get("locator")})
    unique = {record["id"]: record for record in records}
    return [unique[key] for key in sorted(unique)]


def source_fingerprint_path(records: object) -> str | None:
    if isinstance(records, list) and records and isinstance(records[0], dict):
        return records[0].get("path")
    return None


def apply_refresh(previous: dict | None, ledger: dict) -> dict:
    if not previous:
        return ledger
    old_by_id = {item.get("id"): item for item in previous.get("entry_points", []) if isinstance(item, dict)}
    for entry in ledger["entry_points"]:
        old = old_by_id.get(entry["id"])
        if old is None:
            continue
        if old.get("source_fingerprints") == entry.get("source_fingerprints"):
            for key in ("enrichment", "analysis_state", "analysis_ready"):
                if key in old:
                    entry[key] = old[key]
        else:
            entry["stale"] = True
            entry["analysis_state"] = "not-analyzed"
            entry["analysis_ready"] = False
            ledger["evidence_gaps"].append(gap(entry["id"], "source-changed", "Source fingerprint changed; re-investigate this entry.", True))
    return ledger


def build(repo: Path) -> dict:
    provider = detect_provider(repo)
    facts = project_facts(repo)
    if provider == "codegraph":
        entries, nodes, edges, variants, terminals, gaps = build_codegraph(repo)
    elif provider == "gitnexus":
        entries, nodes, edges, variants, terminals, gaps = build_gitnexus(repo)
    else:
        entries, nodes, edges, variants, terminals, gaps = [], [], [], [], [], []
    divergence, rejoin, cycles = derived_edges(variants, edges)
    if provider == "codegraph":
        cycles.extend(codegraph_cycle_edges(repo, {item["id"] for item in nodes}))
        cycles.sort(key=lambda item: (item["from"], item["to"], item.get("path_ref") or ""))
    source = source_fingerprint(repo, provider) if provider != "unknown" else None
    ledger = {
        "schemaVersion": SCHEMA_VERSION, "generated_at": now_iso(), "provider": {
            "id": provider, "fingerprint": source, "locked": locked_provider(repo) == provider,
        },
        "project": {
            "shapes": facts["shapes"], "frameworks": facts["frameworks"],
            "deployable_blocks": facts["deployable_blocks"],
            "source_fingerprints": [source] if source else [],
            "external_relationships": facts["external_relationships"],
        },
        "runtime_surfaces": surfaces_for(entries, facts), "entry_points": sorted(entries, key=lambda item: item["id"]),
        "topology_nodes": sorted(nodes, key=lambda item: item["id"]), "topology_edges": sorted(edges, key=lambda item: item["id"]),
        "path_variants": sorted(variants, key=lambda item: item["id"]), "terminals": sorted(terminals, key=lambda item: item["id"]),
        "divergence_edges": divergence, "rejoin_edges": rejoin, "cycle_edges": cycles,
        "evidence": evidence_records(provider, entries, facts), "evidence_gaps": sorted(gaps, key=lambda item: item["id"]),
    }
    target = path_for(repo)
    previous = None
    if target.is_file():
        try:
            previous = json.loads(target.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            pass
    return apply_refresh(previous, ledger)


def validate(ledger: dict) -> list[str]:
    errors: list[str] = []
    if ledger.get("schemaVersion") != SCHEMA_VERSION:
        errors.append(f"schemaVersion must be {SCHEMA_VERSION}")
    provider = ledger.get("provider")
    if not isinstance(provider, dict) or not provider.get("id"):
        errors.append("provider metadata is required")
    def ids(key: str) -> set[str]:
        values = ledger.get(key)
        if not isinstance(values, list):
            errors.append(f"{key} must be an array")
            return set()
        result = [item.get("id") for item in values if isinstance(item, dict)]
        if len(result) != len(values) or any(not value for value in result):
            errors.append(f"{key} entries need ids")
        if len(set(result)) != len(result):
            errors.append(f"{key} contains duplicate ids")
        return {str(value) for value in result if value}
    surfaces = ids("runtime_surfaces"); entries = ids("entry_points"); nodes = ids("topology_nodes")
    edges = ids("topology_edges"); variants = ids("path_variants"); terminals = ids("terminals"); evidence = ids("evidence")
    for item in ledger.get("evidence", []):
        if isinstance(item, dict) and not item.get("provider"):
            errors.append(f"evidence {item.get('id')}: missing provider provenance")
    for entry in ledger.get("entry_points", []):
        if not isinstance(entry, dict):
            continue
        if entry.get("surface_ref") not in surfaces:
            errors.append(f"entry {entry.get('id')}: dangling surface_ref")
        if not entry.get("provider_ids") or not entry.get("evidence_refs"):
            errors.append(f"entry {entry.get('id')}: missing provider provenance")
        for ref in entry.get("evidence_refs", []):
            if ref not in evidence:
                errors.append(f"entry {entry.get('id')}: dangling evidence_ref {ref}")
        if entry.get("analysis_ready") and any(
            gap.get("entry_ref") == entry.get("id") and gap.get("required")
            for gap in ledger.get("evidence_gaps", []) if isinstance(gap, dict)
        ):
            errors.append(f"entry {entry.get('id')}: analysis_ready despite required evidence gaps")
    for surface in ledger.get("runtime_surfaces", []):
        if not isinstance(surface, dict):
            continue
        if surface.get("kind") not in SURFACE_KINDS:
            errors.append(f"surface {surface.get('id')}: invalid kind")
        for entry_id in surface.get("entry_refs", []):
            if entry_id not in entries:
                errors.append(f"surface {surface.get('id')}: dangling entry_ref {entry_id}")
    for edge in ledger.get("topology_edges", []):
        if not isinstance(edge, dict):
            continue
        if edge.get("from") not in nodes or edge.get("to") not in nodes:
            errors.append(f"edge {edge.get('id')}: dangling topology node")
        if not edge.get("provider_ids"):
            errors.append(f"edge {edge.get('id')}: missing provider provenance")
    terminal_by_id = {item.get("id"): item for item in ledger.get("terminals", []) if isinstance(item, dict)}
    for variant in ledger.get("path_variants", []):
        if not isinstance(variant, dict):
            continue
        if variant.get("entry_ref") not in entries:
            errors.append(f"path {variant.get('id')}: dangling entry_ref")
        ordered = variant.get("ordered_nodes")
        if not isinstance(ordered, list) or not ordered or any(node not in nodes for node in ordered):
            errors.append(f"path {variant.get('id')}: invalid ordered_nodes")
        terminal = terminal_by_id.get(variant.get("terminal_ref"))
        if terminal is None:
            errors.append(f"path {variant.get('id')}: dangling terminal_ref")
        elif ordered and terminal.get("node_ref") != ordered[-1]:
            errors.append(f"path {variant.get('id')}: terminal does not end ordered path")
    for edge_id in ledger.get("divergence_edges", []) + ledger.get("rejoin_edges", []):
        if edge_id not in edges:
            errors.append(f"derived topology edge {edge_id}: dangling edge reference")
    for marker in ledger.get("cycle_edges", []):
        if not isinstance(marker, dict) or marker.get("from") not in nodes or marker.get("to") not in nodes:
            errors.append("cycle edge: dangling topology node")
    for terminal in ledger.get("terminals", []):
        if isinstance(terminal, dict) and (terminal.get("node_ref") not in nodes or terminal.get("entry_ref") not in entries):
            errors.append(f"terminal {terminal.get('id')}: dangling topology reference")
    return errors


def write(repo: Path, ledger: dict) -> Path:
    target = path_for(repo); target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(dump_json(ledger), encoding="utf-8")
    return target


def prepare_if_available(repo: Path) -> tuple[Path | None, list[str]]:
    """Refresh provider evidence when the selected provider has local input.

    Callers use this at the start of harvest/revise and analysis preparation.
    It deliberately returns ``None`` rather than creating an empty ledger when
    a locked provider is not available: provider readiness remains the graph
    subsystem's responsibility and an absent index must not erase useful prior
    evidence.
    """
    provider = detect_provider(repo)
    if provider not in {"codegraph", "gitnexus"} or source_fingerprint(repo, provider) is None:
        return None, []
    ledger = build(repo)
    errors = validate(ledger)
    if errors:
        return None, errors
    return write(repo, ledger), []


def run_prepare(repo: Path, as_json: bool) -> int:
    ledger = build(repo); errors = validate(ledger)
    if errors:
        for error in errors: print(f"error: {error}", file=__import__("sys").stderr)
        return 1
    target = write(repo, ledger)
    if as_json:
        print(dump_json(ledger), end="")
    else:
        print(f"Prepared {target} — {len(ledger['runtime_surfaces'])} surface(s), {len(ledger['entry_points'])} entry point(s), {len(ledger['path_variants'])} path variant(s).")
    return 0


def run_import(repo: Path, source: Path) -> int:
    if not source.is_file(): return fail(f"enrichment file not found: {source}", 1)
    try: enrichment = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc: return fail(f"invalid enrichment JSON: {exc}", 1)
    target = path_for(repo)
    if not target.is_file(): return fail(f"flow evidence not found: {target}; run prepare first", 1)
    try: ledger = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc: return fail(f"invalid flow evidence: {exc}", 1)
    if not isinstance(enrichment, dict): return fail("enrichment must be a JSON object", 1)
    entries = {item.get("id"): item for item in ledger.get("entry_points", []) if isinstance(item, dict)}
    changed = 0
    resolved: set[str] = set()
    for patch in enrichment.get("entry_points", enrichment.get("entries", [])):
        if not isinstance(patch, dict) or patch.get("id") not in entries:
            return fail(f"unknown evidence entry: {patch.get('id') if isinstance(patch, dict) else patch}", 1)
        entry = entries[patch["id"]]
        entry["enrichment"] = patch.get("enrichment", patch)
        resolved.update(str(value) for value in patch.get("resolved_gaps", []) if value)
        if patch.get("analysis_ready") is True:
            entry["analysis_ready"] = True
        changed += 1
    if resolved:
        ledger["evidence_gaps"] = [item for item in ledger.get("evidence_gaps", [])
                                   if item.get("id") not in resolved and item.get("type") not in resolved]
    extras = enrichment.get("evidence", [])
    if extras:
        known = {item.get("id") for item in ledger.get("evidence", []) if isinstance(item, dict)}
        for item in extras:
            if not isinstance(item, dict) or not item.get("id") or not item.get("provider"):
                return fail("imported evidence requires id and provider provenance", 1)
            if item["id"] not in known:
                ledger["evidence"].append(item); known.add(item["id"])
    errors = validate(ledger)
    if errors:
        for error in errors: print(f"error: {error}", file=__import__("sys").stderr)
        return 1
    write(repo, ledger); print(f"Imported enrichment for {changed} entry point(s) into {target}.")
    return 0


def run_status(repo: Path, as_json: bool) -> int:
    target = path_for(repo)
    if not target.is_file(): return fail(f"flow evidence not found: {target}; run prepare first", 1)
    try: ledger = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc: return fail(f"invalid flow evidence: {exc}", 1)
    gaps = ledger.get("evidence_gaps", [])
    result = {
        "schemaVersion": SCHEMA_VERSION, "provider": ledger.get("provider"),
        "complete_entries": sorted(item["id"] for item in ledger.get("entry_points", []) if isinstance(item, dict) and item.get("analysis_ready")),
        "stale_entries": sorted(item["id"] for item in ledger.get("entry_points", []) if isinstance(item, dict) and item.get("stale")),
        "ambiguous_entries": sorted(item["id"] for item in ledger.get("entry_points", []) if isinstance(item, dict) and item.get("trigger", {}).get("kind") == "internal"),
        "unresolved_entries": sorted({item.get("entry_ref") for item in gaps if isinstance(item, dict) and item.get("required") and item.get("entry_ref")}),
        "evidence_gaps": gaps,
    }
    if as_json: print(dump_json(result), end="")
    else: print(f"Flow preflight: {target}\nComplete: {len(result['complete_entries'])}; stale: {len(result['stale_entries'])}; ambiguous: {len(result['ambiguous_entries'])}; unresolved: {len(result['unresolved_entries'])}.")
    return 0


def run_validate(repo: Path) -> int:
    target = path_for(repo)
    if not target.is_file(): return fail(f"flow evidence not found: {target}; run prepare first", 1)
    try: ledger = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc: return fail(f"invalid flow evidence: {exc}", 1)
    errors = validate(ledger)
    if errors:
        for error in errors: print(f"error: {error}", file=__import__("sys").stderr)
        return 1
    print("flow preflight ok"); return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    prepare = sub.add_parser("prepare"); prepare.add_argument("--repo", required=True, type=Path); prepare.add_argument("--json", action="store_true")
    import_ = sub.add_parser("import"); import_.add_argument("--repo", required=True, type=Path); import_.add_argument("--input", "--evidence", "--analysis", dest="input", required=True, type=Path)
    status = sub.add_parser("status"); status.add_argument("--repo", required=True, type=Path); status.add_argument("--json", action="store_true")
    validate_ = sub.add_parser("validate"); validate_.add_argument("--repo", required=True, type=Path)
    args = parser.parse_args(argv)
    if not args.repo.is_dir(): return fail(f"not a directory: {args.repo}", 2)
    if args.command == "prepare": return run_prepare(args.repo, args.json)
    if args.command == "import": return run_import(args.repo, args.input)
    if args.command == "status": return run_status(args.repo, args.json)
    return run_validate(args.repo)


if __name__ == "__main__":
    raise SystemExit(main())
