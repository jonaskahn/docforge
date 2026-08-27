#!/usr/bin/env python3
"""Adaptive flow-analysis ledger: prepare, import, decide, status, validate, audit.

The persistent ``.docforge/flow-analysis.json`` pack is coordination metadata,
not reader-facing prose.  Schema v3 records evidence-specific flow cards and
their document designs.  V1/V2 packs remain readable, but are migrated without
inventing facts and are marked ``legacy-needs-analysis``.
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from runtime.common.python._util import dump_json, fail, load_manifest
from runtime.common.python import scale

ANALYSIS_REL = Path(".docforge/flow-analysis.json")
SCHEMA_VERSION = 3
LEGACY_SCHEMA_VERSIONS = {1, 2}
EVIDENCE_WORKERS_BY_SCALE = {"small": 3, "medium": 6, "large": 8}
PROPOSAL_AGENTS_BY_SCALE = {"small": 2, "medium": 3, "large": 4}
RESEARCH_POLICIES = {"official-primary", "official-only", "off"}
FLOW_CHARACTERISTICS = {
    "request-command", "event-message", "scheduled-batch",
    "lifecycle-stateful", "streaming-interactive", "fan-out-orchestration",
    "resource-lifecycle",
}
FLOW_STATES = {
    "not-analyzed", "legacy-needs-analysis", "analyzing", "ready", "audited",
}
DECISIONS = {"proposed", "selected", "declined"}
TRIGGER_KINDS = {"http", "queue", "schedule", "cli", "ui", "internal"}
MODULES = {
    "state", "transaction", "consistency", "idempotency", "ordering",
    "deduplication", "timing", "backpressure", "security", "observability",
    "recovery", "compensation", "residual-state",
}
FAILURE_CATEGORIES = {
    "decision-rejected", "awaited-event-timeout", "timeout", "interruption", "cancellation",
}
DIAGRAM_FORMS = {"sequenceDiagram", "flowchart", "stateDiagram-v2", "text"}
FLOW_ID = re.compile(r"^flow-[a-z0-9][a-z0-9-]*$")
STEP_REF_KEYS = {
    "step", "step_order", "from_step", "to_step", "rejoin_step", "join_step",
}


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def analysis_path(repo: Path) -> Path:
    return repo / ANALYSIS_REL


def normalize_analysis(data: dict) -> dict:
    """Normalize through the public serializer for Python/JavaScript parity."""
    return json.loads(dump_json(data))


def _migrate_legacy(data: dict, repo: Path | None = None) -> dict:
    """Promote v1/v2 into a v3 legacy envelope without synthesizing facts."""
    source = data.get("source") or (str(repo.resolve()) if repo else "legacy-analysis")
    migrated_flows = []
    for position, old in enumerate(data.get("flows", []), start=1):
        if not isinstance(old, dict):
            continue
        raw_id = str(old.get("id") or old.get("flowId") or f"flow-legacy-{position}")
        if not FLOW_ID.fullmatch(raw_id):
            slug = re.sub(r"[^a-z0-9]+", "-", raw_id.lower()).strip("-") or f"legacy-{position}"
            raw_id = f"flow-{slug}"
        migrated_flows.append({
            "id": raw_id,
            "name": str(old.get("name") or old.get("title") or raw_id),
            "analysis_state": "legacy-needs-analysis",
            "decision": "proposed",
            "parent_flow": None,
            "legacy_evidence": old,
        })
    old_workers = data.get("workers") if isinstance(data.get("workers"), dict) else {}
    old_audit = data.get("audit") if isinstance(data.get("audit"), dict) else {}
    return {
        "schemaVersion": SCHEMA_VERSION,
        "source": str(source),
        "generated_at": now_iso(),
        "research_policy": data.get("research_policy"),
        "workers": {
            "evidence": old_workers.get("evidence", 3),
            "proposals": old_workers.get("proposals", 2),
        },
        "audit": {
            "status": old_audit.get("status", "pending"),
            "verdict": old_audit.get("verdict"),
            "report": old_audit.get("report"),
        },
        "flows": migrated_flows,
    }


def read_analysis(repo: Path) -> dict:
    path = analysis_path(repo)
    if not path.is_file():
        raise ValueError(f"flow analysis not found: {path}; run flow_analysis prepare/import first")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid flow analysis {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"flow analysis must be a JSON object: {path}")
    version = data.get("schemaVersion", 1)
    if version in LEGACY_SCHEMA_VERSIONS:
        return _migrate_legacy(data, repo)
    if version != SCHEMA_VERSION:
        raise ValueError(f"flow analysis must use schemaVersion 1, 2, or {SCHEMA_VERSION}: {path}")
    return data


def write_analysis(repo: Path, data: dict) -> None:
    data["schemaVersion"] = SCHEMA_VERSION
    data["generated_at"] = now_iso()
    target = analysis_path(repo)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(dump_json(normalize_analysis(data)), encoding="utf-8")


def _manifest_scale(manifest: dict | None) -> str | None:
    record = (manifest or {}).get("project", {}).get("scale")
    value = record.get("class") if isinstance(record, dict) else None
    return value if value in EVIDENCE_WORKERS_BY_SCALE else None


def _scale_class(repo: Path, manifest_path: str | None = None) -> str:
    if manifest_path:
        value = _manifest_scale(load_manifest(Path(manifest_path)))
        if value:
            return value
    manifest = repo / ".docforge" / "manifest.json"
    if manifest.is_file():
        try:
            value = _manifest_scale(load_manifest(manifest))
            if value:
                return value
        except ValueError:
            pass
    return scale.compute_scale(repo)["class"]


def default_analysis(repo: Path, manifest_path: str | None = None) -> dict:
    klass = _scale_class(repo, manifest_path)
    return {
        "schemaVersion": SCHEMA_VERSION,
        "source": str(repo.resolve()),
        "generated_at": now_iso(),
        "research_policy": None,
        "workers": {
            "evidence": EVIDENCE_WORKERS_BY_SCALE.get(klass, 3),
            "proposals": PROPOSAL_AGENTS_BY_SCALE.get(klass, 2),
        },
        "audit": {"status": "pending", "verdict": None, "report": None},
        "flows": [],
    }


def _validate_step_references(flow_id: str, patterns: object, orders: set[int]) -> list[str]:
    errors: list[str] = []
    if not isinstance(patterns, dict):
        return [f"flow {flow_id}: flow_patterns must be an object"]
    for kind, records in patterns.items():
        if not isinstance(records, list):
            errors.append(f"flow {flow_id}: flow_patterns.{kind} must be an array")
            continue
        for position, record in enumerate(records, start=1):
            if not isinstance(record, dict):
                errors.append(f"flow {flow_id}: flow_patterns.{kind}[{position}] must be an object")
                continue
            for key in STEP_REF_KEYS.intersection(record):
                value = record[key]
                refs = value if isinstance(value, list) else [value]
                for ref in refs:
                    if isinstance(ref, int) and ref not in orders:
                        errors.append(
                            f"flow {flow_id}: flow_patterns.{kind}[{position}].{key} "
                            f"references missing step {ref}"
                        )
    return errors


def validate_analysis(data: dict, repo: Path | None = None, allow_empty: bool = False) -> list[str]:
    """Validate v3 structure plus cross-references that JSON Schema cannot."""
    errors: list[str] = []
    if data.get("schemaVersion") != SCHEMA_VERSION:
        errors.append(f"schemaVersion must be {SCHEMA_VERSION}")
    if not str(data.get("source") or "").strip():
        errors.append("source must be a non-empty string")
    if data.get("research_policy") not in RESEARCH_POLICIES | {None}:
        errors.append("research_policy must be official-primary, official-only, off, or null")
    workers = data.get("workers")
    if not isinstance(workers, dict) or not all(
        isinstance(workers.get(key), int) and workers[key] > 0 for key in ("evidence", "proposals")
    ):
        errors.append("workers must contain positive evidence and proposals counts")
    audit = data.get("audit")
    if not isinstance(audit, dict):
        errors.append("audit must be an object")
    else:
        if audit.get("status") not in {"pending", "passed", "failed"}:
            errors.append("audit.status must be pending, passed, or failed")
        if audit.get("verdict") not in {None, "PASS", "FAIL"}:
            errors.append("audit.verdict must be PASS, FAIL, or null")
        if audit.get("verdict") == "PASS" and audit.get("status") != "passed":
            errors.append("audit.verdict PASS requires audit.status passed")
        if audit.get("verdict") == "FAIL" and audit.get("status") != "failed":
            errors.append("audit.verdict FAIL requires audit.status failed")
    flows = data.get("flows")
    if not isinstance(flows, list):
        errors.append("flows must be an array")
        return errors
    if not flows and not allow_empty:
        errors.append("flows must contain at least one analyzed flow")

    flow_ids: set[str] = set()
    proposal_ids: set[str] = set()
    child_ids: set[str] = set()
    for position, flow in enumerate(flows, start=1):
        if not isinstance(flow, dict):
            errors.append(f"flows[{position}] must be an object")
            continue
        flow_id = str(flow.get("id") or "")
        if not FLOW_ID.fullmatch(flow_id):
            errors.append(f"flow {flow_id or position}: invalid id")
        if flow_id in flow_ids:
            errors.append(f"duplicate flow id: {flow_id}")
        flow_ids.add(flow_id)
        if not str(flow.get("name") or "").strip():
            errors.append(f"flow {flow_id}: name is required")
        state = flow.get("analysis_state")
        if state not in FLOW_STATES:
            errors.append(f"flow {flow_id}: invalid analysis_state {state!r}")
        if flow.get("decision", "proposed") not in DECISIONS:
            errors.append(f"flow {flow_id}: invalid decision {flow.get('decision')!r}")
        if state == "legacy-needs-analysis":
            if not isinstance(flow.get("legacy_evidence"), dict):
                errors.append(f"flow {flow_id}: legacy_evidence is required for legacy migration")
            continue
        for required in (
            "reader_question", "characteristics", "trigger", "guarantee",
            "terminal_outcomes", "actors", "steps", "document_design",
        ):
            if required not in flow:
                errors.append(f"flow {flow_id}: missing required field '{required}'")
        characteristics = flow.get("characteristics", [])
        if not isinstance(characteristics, list) or not characteristics:
            errors.append(f"flow {flow_id}: characteristics must be a non-empty array")
        else:
            unknown = sorted(set(characteristics) - FLOW_CHARACTERISTICS)
            if unknown:
                errors.append(f"flow {flow_id}: unknown characteristics: {', '.join(unknown)}")
        trigger = flow.get("trigger")
        if not isinstance(trigger, dict) or trigger.get("kind") not in TRIGGER_KINDS or not str(trigger.get("signature") or "").strip():
            errors.append(f"flow {flow_id}: trigger requires kind and signature")
        if not str(flow.get("guarantee") or "").strip():
            errors.append(f"flow {flow_id}: guarantee is required")
        outcomes = flow.get("terminal_outcomes")
        if not isinstance(outcomes, list) or not outcomes:
            errors.append(f"flow {flow_id}: terminal_outcomes must be non-empty")
        actors = flow.get("actors")
        if not isinstance(actors, dict) or any(key not in actors for key in ("initiator", "visible", "hidden")):
            errors.append(f"flow {flow_id}: actors requires initiator, visible, and hidden")
        steps = flow.get("steps")
        orders: set[int] = set()
        if not isinstance(steps, list) or not steps:
            errors.append(f"flow {flow_id}: steps must be non-empty")
        else:
            for step in steps:
                if not isinstance(step, dict):
                    errors.append(f"flow {flow_id}: each step must be an object")
                    continue
                order = step.get("order")
                if not isinstance(order, int) or order < 1 or order in orders:
                    errors.append(f"flow {flow_id}: step order {order!r} is invalid or duplicate")
                else:
                    orders.add(order)
                for required in ("name", "actor", "file", "evidence"):
                    if not str(step.get(required) or "").strip():
                        errors.append(f"flow {flow_id}: step {order} missing {required}")
                file_name = str(step.get("file") or "")
                if repo is not None and file_name and not (repo / file_name).is_file():
                    errors.append(f"flow {flow_id}: step {order} references missing file {file_name}")
            if orders and orders != set(range(1, max(orders) + 1)):
                errors.append(f"flow {flow_id}: step order must be contiguous from 1")
        errors.extend(_validate_step_references(flow_id, flow.get("flow_patterns", {}), orders))
        for module in flow.get("modules", []):
            if not isinstance(module, dict) or module.get("name") not in MODULES or not str(module.get("evidence") or "").strip():
                errors.append(f"flow {flow_id}: each module requires a supported name and evidence")
        for failure in flow.get("failures", []):
            if not isinstance(failure, dict) or failure.get("category") not in FAILURE_CATEGORIES:
                errors.append(f"flow {flow_id}: each failure requires a supported category")
                continue
            failure_file = str(failure.get("file") or "")
            if not failure_file:
                errors.append(f"flow {flow_id}: failure file is required")
            elif repo is not None and not (repo / failure_file).is_file():
                errors.append(f"flow {flow_id}: failure references missing file {failure_file}")
        design = flow.get("document_design")
        if not isinstance(design, dict) or not isinstance(design.get("section_order"), list) or not design.get("section_order"):
            errors.append(f"flow {flow_id}: document_design.section_order must be non-empty")
        elif len(design["section_order"]) != len(set(design["section_order"])):
            errors.append(f"flow {flow_id}: document_design.section_order contains duplicates")
        diagrams = design.get("diagrams", []) if isinstance(design, dict) else []
        if not isinstance(diagrams, list):
            errors.append(f"flow {flow_id}: document_design.diagrams must be an array")
        else:
            sections = set(design.get("section_order", [])) if isinstance(design, dict) else set()
            for diagram in diagrams:
                if not isinstance(diagram, dict) or diagram.get("form") not in DIAGRAM_FORMS or diagram.get("section") not in sections or not str(diagram.get("question") or "").strip():
                    errors.append(f"flow {flow_id}: diagram references a section outside section_order")
        for proposal in flow.get("decomposition_proposals", []):
            if not isinstance(proposal, dict):
                errors.append(f"flow {flow_id}: decomposition proposal must be an object")
                continue
            proposal_id = str(proposal.get("id") or "")
            if not proposal_id or proposal_id in proposal_ids:
                errors.append(f"flow {flow_id}: duplicate or empty decomposition proposal id {proposal_id!r}")
            proposal_ids.add(proposal_id)
            proposed = proposal.get("proposed_flows", [])
            if proposal.get("approved") and not proposed:
                errors.append(f"flow {flow_id}: approved proposal {proposal_id} has no proposed_flows")
            for child in proposed:
                child_id = str(child.get("id") or "") if isinstance(child, dict) else ""
                if not FLOW_ID.fullmatch(child_id) or child_id == flow_id or child_id in child_ids:
                    errors.append(f"flow {flow_id}: invalid or duplicate proposed child id {child_id!r}")
                child_ids.add(child_id)

    parents = {flow.get("id"): flow.get("parent_flow") for flow in flows if isinstance(flow, dict)}
    for flow_id, parent in parents.items():
        if parent is not None and parent not in flow_ids:
            errors.append(f"flow {flow_id}: parent_flow {parent!r} does not exist")
        seen = {flow_id}
        cursor = parent
        while cursor is not None:
            if cursor in seen:
                errors.append(f"flow {flow_id}: decomposition cycle detected")
                break
            seen.add(cursor)
            cursor = parents.get(cursor)
    return errors


def run_prepare(repo: Path, manifest_path: str | None) -> int:
    analysis = default_analysis(repo, manifest_path)
    errors = validate_analysis(analysis, allow_empty=True)
    if errors:
        for error in errors:
            print(f"error: {error}", file=__import__("sys").stderr)
        return 1
    print(dump_json(analysis), end="")
    return 0


def run_import(repo: Path, source_path: str) -> int:
    source = Path(source_path)
    if not source.is_file():
        return fail(f"analysis file not found: {source}", 1)
    try:
        data = json.loads(source.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return fail(f"invalid analysis JSON: {exc}", 1)
    if not isinstance(data, dict):
        return fail("analysis must be a JSON object", 1)
    if data.get("schemaVersion", 1) in LEGACY_SCHEMA_VERSIONS:
        data = _migrate_legacy(data, repo)
    errors = validate_analysis(data, repo=repo, allow_empty=False)
    if errors:
        for error in errors:
            print(f"error: {error}", file=__import__("sys").stderr)
        return 1
    write_analysis(repo, data)
    print(f"Imported flow analysis to {analysis_path(repo)}")
    return 0


def run_decide(
    repo: Path,
    select: list[str],
    decline: list[str],
    approve_decomposition: list[str],
    research_policy: str,
) -> int:
    data = read_analysis(repo)
    by_id = {flow.get("id"): flow for flow in data.get("flows", [])}
    overlap = set(select) & set(decline)
    if overlap:
        return fail(f"flow ids cannot be both selected and declined: {', '.join(sorted(overlap))}", 1)
    for flow_id in select + decline:
        if flow_id not in by_id:
            return fail(f"unknown flow id: {flow_id}", 1)
    proposals = {
        proposal.get("id"): proposal
        for flow in data.get("flows", [])
        for proposal in flow.get("decomposition_proposals", [])
        if isinstance(proposal, dict)
    }
    for proposal_id in approve_decomposition:
        if proposal_id not in proposals:
            return fail(f"unknown decomposition proposal id: {proposal_id}", 1)
    for flow in data.get("flows", []):
        flow["decision"] = "selected" if flow.get("id") in select else "declined"
    for proposal in proposals.values():
        proposal["approved"] = proposal.get("id") in approve_decomposition
    data["research_policy"] = research_policy
    write_analysis(repo, data)
    print(
        f"Recorded {len(select)} selected flow(s), {len(approve_decomposition)} approved "
        f"decomposition(s); research policy: {research_policy}."
    )
    return 0


def run_status(repo: Path, as_json: bool) -> int:
    data = read_analysis(repo)
    selected = [flow for flow in data.get("flows", []) if flow.get("decision") == "selected"]
    declined = [flow for flow in data.get("flows", []) if flow.get("decision") == "declined"]
    unresolved = [
        {"flow_id": flow.get("id"), "gap": gap}
        for flow in data.get("flows", [])
        for gap in flow.get("evidence_gaps", [])
    ]
    if as_json:
        print(dump_json({
            "schemaVersion": SCHEMA_VERSION,
            "generated_at": data.get("generated_at"),
            "selected_flows": selected,
            "declined_flows": declined,
            "unresolved_gaps": unresolved,
            "research_policy": data.get("research_policy"),
            "audit": data.get("audit"),
        }), end="")
    else:
        print(f"Flow analysis: {analysis_path(repo)}")
        print(f"Selected flows: {len(selected)}; declined: {len(declined)}; unresolved gaps: {len(unresolved)}")
        print(f"Research policy: {data.get('research_policy')}")
        audit = data.get("audit", {})
        print(f"Pack audit: {audit.get('status')} ({audit.get('verdict') or 'pending'})")
    return 0


def run_validate(repo: Path) -> int:
    data = read_analysis(repo)
    errors = validate_analysis(data, repo=repo)
    if errors:
        for error in errors:
            print(f"error: {error}", file=__import__("sys").stderr)
        return 1
    print("flow analysis ok")
    return 0


def run_audit(repo: Path, verdict: str, report: str) -> int:
    data = read_analysis(repo)
    report_path = Path(report)
    if not report_path.is_file() or not report_path.read_text(encoding="utf-8").strip():
        return fail(f"audit report must be a non-empty file: {report_path}", 1)
    errors = validate_analysis(data, repo=repo)
    if verdict == "PASS":
        selected = [flow for flow in data.get("flows", []) if flow.get("decision") == "selected"]
        if not selected:
            return fail("cannot pass flow-pack audit without selected flows", 1)
        unready = [flow.get("id") for flow in selected if flow.get("analysis_state") not in {"ready", "audited"}]
        if unready:
            return fail(f"cannot pass flow-pack audit; analysis is not ready: {', '.join(unready)}", 1)
        if errors:
            return fail("cannot pass flow-pack audit while analysis validation fails", 1)
    data["audit"] = {
        "status": "passed" if verdict == "PASS" else "failed",
        "verdict": verdict,
        "report": str(report_path),
    }
    if verdict == "PASS":
        for flow in data.get("flows", []):
            if flow.get("decision") == "selected":
                flow["analysis_state"] = "audited"
    write_analysis(repo, data)
    print(f"Recorded flow-pack audit {verdict}.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    prepare = sub.add_parser("prepare")
    prepare.add_argument("--repo", required=True, type=Path)
    prepare.add_argument("--manifest")
    prepare.add_argument("--json", action="store_true")
    import_ = sub.add_parser("import")
    import_.add_argument("--repo", required=True, type=Path)
    import_.add_argument("--analysis", required=True)
    decide = sub.add_parser("decide")
    decide.add_argument("--repo", required=True, type=Path)
    decide.add_argument("--select", nargs="*", default=[])
    decide.add_argument("--decline", nargs="*", default=[])
    decide.add_argument("--approve-decomposition", nargs="*", default=[])
    decide.add_argument("--research-policy", required=True, choices=sorted(RESEARCH_POLICIES))
    status = sub.add_parser("status")
    status.add_argument("--repo", required=True, type=Path)
    status.add_argument("--json", action="store_true")
    validate = sub.add_parser("validate")
    validate.add_argument("--repo", required=True, type=Path)
    audit = sub.add_parser("audit")
    audit.add_argument("--repo", required=True, type=Path)
    audit.add_argument("--verdict", required=True, choices=["PASS", "FAIL"])
    audit.add_argument("--report", required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "prepare":
            return run_prepare(args.repo, args.manifest)
        if args.command == "import":
            return run_import(args.repo, args.analysis)
        if args.command == "decide":
            return run_decide(
                args.repo, args.select, args.decline,
                args.approve_decomposition, args.research_policy,
            )
        if args.command == "status":
            return run_status(args.repo, args.json)
        if args.command == "validate":
            return run_validate(args.repo)
        if args.command == "audit":
            return run_audit(args.repo, args.verdict, args.report)
        return fail(f"unknown command: {args.command}", 2)
    except ValueError as exc:
        return fail(str(exc), 1)


if __name__ == "__main__":
    raise SystemExit(main())
