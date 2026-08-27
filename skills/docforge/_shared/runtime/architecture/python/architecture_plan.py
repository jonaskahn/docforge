#!/usr/bin/env python3
"""Architecture plan ledger: prepare / import / decide / status / validate / audit.

Paired with runtime/architecture/js/plan.js. The architecture ledger
(`.docforge/architecture-plan.json`, schema 1.0) is the coordination record
for adaptive deep architecture generation: it owns the frozen evidence
inventory, proposed documents, research policy, adjudication results, and
pack-audit state. It is coordination metadata, not reader-facing prose.

Both runtimes produce byte-identical normalized JSON.
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from runtime.common.python._util import dump_json, fail, load_manifest
from runtime.common.python import scale
from runtime.catalog.python import query_catalog
from runtime.catalog.python.detect_profiles import detect as detect_profiles
from runtime.catalog.python.detect_profiles import inventory as inventory_files

PLAN_REL = Path(".docforge/architecture-plan.json")
SCHEMA_VERSION = "1.0"
PLAN_VERSION = "1.0"
# Parallel evidence workers per scale class (see planning.md "Parallel
# evidence discovery").
EVIDENCE_WORKERS_BY_SCALE = {"small": 3, "medium": 6, "large": 8}
# Proposal agents per scale class (see planning.md "Independent document-pack
# proposals").
PROPOSAL_AGENTS_BY_SCALE = {"small": 2, "medium": 3, "large": 4}
RESEARCH_POLICIES = {"official-primary", "official-only", "off"}
EXTERNAL_KINDS = {"standard", "official-doc", "vendor-doc", "primary-research"}
EXTERNAL_RELATIONS = {"primary-source", "supporting-source", "method", "terminology"}
DOCUMENT_STATES = {"proposed", "selected", "declined"}
RFC3339 = re.compile(
    r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(\.\d+)?(Z|[+-]\d\d:\d\d)$"
)
URL = re.compile(r"^https?://")
BATCH_RE = re.compile(r"^[a-z][a-z0-9-]*$")


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def plan_path(repo: Path) -> Path:
    return repo / PLAN_REL


def read_plan(repo: Path) -> dict:
    path = plan_path(repo)
    if not path.is_file():
        raise ValueError(f"architecture plan not found: {path}; run architecture_plan prepare first")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid architecture plan {path}: {exc}") from exc
    if not isinstance(data, dict) or data.get("schema") != SCHEMA_VERSION:
        raise ValueError(f"architecture plan must use schema {SCHEMA_VERSION}: {path}")
    return data


def write_plan(repo: Path, plan: dict) -> None:
    plan["schema"] = SCHEMA_VERSION
    plan["generated_at"] = now_iso()
    path = plan_path(repo)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dump_json(normalize_plan(plan)), encoding="utf-8")


def normalize_plan(plan: dict) -> dict:
    """Deterministic key order and serialization for byte-identical parity."""
    return json.loads(dump_json(plan))


def _scale_class(repo: Path) -> str:
    try:
        manifest = load_manifest(repo / ".docforge" / "manifest.json")
        scale_rec = manifest.get("project", {}).get("scale")
        klass = scale_rec.get("class") if isinstance(scale_rec, dict) else None
        if klass in EVIDENCE_WORKERS_BY_SCALE:
            return klass
    except ValueError:
        pass
    detected = scale.compute_scale(repo)
    return detected["class"]


def _detect_layout_tier_profiles(repo: Path) -> dict:
    manifest_path = repo / ".docforge" / "manifest.json"
    if manifest_path.is_file():
        try:
            manifest = load_manifest(manifest_path)
        except ValueError:
            manifest = None
    else:
        manifest = None
    if manifest is not None:
        project = manifest.get("project", {})
        scale_rec = project.get("scale", {})
        layout = scale_rec.get("layout") or "standard"
        tier = project.get("tier") or "diligence"
        profiles = project.get("profiles", {})
        graph = manifest.get("graph")
        return {
            "scale": scale_rec.get("class") or _scale_class(repo),
            "layout": layout,
            "tier": tier,
            "profiles": profiles,
            "graph_lock": graph if isinstance(graph, dict) else None,
        }
    klass = _scale_class(repo)
    files = inventory_files(repo)
    detections = detect_profiles(repo, persist=False, files=files)
    confirmed = [item["id"] for item in detections if item.get("confidence") == "confirmed"]
    profiles: dict[str, list[str]] = {"shapes": [], "platforms": [], "frameworks": [], "concerns": [], "audiences": []}
    for item in detections:
        if item.get("confidence") != "confirmed":
            continue
        dimension = item.get("dimension")
        if dimension in profiles:
            profiles[dimension].append(item["id"])
    return {
        "scale": klass,
        "layout": scale.LAYOUT_BY_CLASS.get(klass, "standard"),
        "tier": "diligence",
        "profiles": profiles,
        "graph_lock": None,
    }


def default_plan(repo: Path) -> dict:
    """A schema-1.0 plan skeleton, populated from repository facts."""
    project = _detect_layout_tier_profiles(repo)
    klass = project["scale"]
    return {
        "schema": SCHEMA_VERSION,
        "project": project,
        "system": {
            "capability": "",
            "drivers": [],
            "actors": [],
            "external_systems": [],
            "deployable_blocks": [],
            "subsystem_candidates": [],
            "deployment_nodes": [],
            "relationships": [],
            "invariants": [],
            "trust_boundaries": [],
            "failure_domains": [],
            "quality_constraints": [],
            "conflicts": [],
        },
        "documents": [],
        "research": {
            "policy": "off",
            "authorized": False,
            "questions": [],
            "sources": [],
        },
        "adjudication": {
            "proposals": [],
            "adjudicator": None,
            "merged": [],
            "omitted": [],
            "expansions": [],
        },
        "audit": {
            "status": "pending",
            "verdict": None,
            "report": None,
        },
        "workers": {
            "evidence": EVIDENCE_WORKERS_BY_SCALE.get(klass, 3),
            "proposals": PROPOSAL_AGENTS_BY_SCALE.get(klass, 2),
        },
        "research_policy": "off",
    }


def validate_plan(plan: dict) -> list[str]:
    """Mechanical schema and relationship validation. Read-only."""
    errors: list[str] = []
    if plan.get("schema") != SCHEMA_VERSION:
        errors.append(f"plan schema must be {SCHEMA_VERSION}")
    project = plan.get("project", {})
    if project.get("scale") not in EVIDENCE_WORKERS_BY_SCALE:
        errors.append(f"project.scale must be one of: {', '.join(sorted(EVIDENCE_WORKERS_BY_SCALE))}")
    if project.get("layout") not in {"standard", "compact"}:
        errors.append("project.layout must be standard or compact")
    system = plan.get("system", {})
    block_ids = {block.get("id") for block in system.get("deployable_blocks", []) if isinstance(block, dict)}
    if len(block_ids) != len(system.get("deployable_blocks", [])):
        errors.append("system.deployable_blocks: duplicate ids")
    for block in system.get("deployable_blocks", []):
        parent = block.get("parent")
        if parent and parent not in block_ids:
            errors.append(f"system.deployable_blocks.{block.get('id')}: parent {parent} is not a block")
    rel_ids = set()
    for rel in system.get("relationships", []):
        rel_ids.add((rel.get("origin"), rel.get("destination")))
        if rel.get("origin") not in block_ids and rel.get("origin") not in system.get("actors", []):
            errors.append(f"relationship origin {rel.get('origin')} is not a block or actor")
        if rel.get("destination") not in block_ids and rel.get("destination") not in system.get("external_systems", []):
            errors.append(f"relationship destination {rel.get('destination')} is not a block or external system")
    subsystem_ids = {c.get("id") for c in system.get("subsystem_candidates", [])}
    if len(subsystem_ids) != len(system.get("subsystem_candidates", [])):
        errors.append("system.subsystem_candidates: duplicate ids")
    doc_ids = set()
    batch_ids = set()
    for doc in plan.get("documents", []):
        doc_id = doc.get("id")
        if doc_id in doc_ids:
            errors.append(f"documents: duplicate id {doc_id}")
        doc_ids.add(doc_id)
        if doc.get("state") not in DOCUMENT_STATES:
            errors.append(f"documents.{doc_id}: invalid state {doc.get('state')}")
        for parent in doc.get("parent_blocks", []):
            if parent not in block_ids:
                errors.append(f"documents.{doc_id}: parent block {parent} is not a block")
        for dependency in doc.get("dependencies", []):
            if dependency not in {d.get("id") for d in plan.get("documents", [])}:
                errors.append(f"documents.{doc_id}: dependency {dependency} is not a document")
        batch = doc.get("batch")
        if isinstance(batch, int) and batch not in batch_ids:
            batch_ids.add(batch)
    research = plan.get("research", {})
    if research.get("policy") not in RESEARCH_POLICIES:
        errors.append(f"research.policy must be one of: {', '.join(sorted(RESEARCH_POLICIES))}")
    if research.get("authorized") and research.get("policy") == "off":
        errors.append("research.authorized is true but research.policy is off")
    source_ids = {source.get("id") for source in research.get("sources", [])}
    if len(source_ids) != len(research.get("sources", [])):
        errors.append("research.sources: duplicate ids")
    for source in research.get("sources", []):
        if source.get("id") not in source_ids:
            continue
        if not URL.match(str(source.get("url") or "")):
            errors.append(f"research.sources.{source.get('id')}: url must be http(s)")
        if source.get("kind") not in EXTERNAL_KINDS:
            errors.append(f"research.sources.{source.get('id')}: invalid kind")
        if not RFC3339.fullmatch(str(source.get("accessed_at") or "")):
            errors.append(f"research.sources.{source.get('id')}: accessed_at must be RFC3339")
    for doc in plan.get("documents", []):
        for ref in doc.get("external_refs", []):
            if ref.get("source_id") not in source_ids:
                errors.append(f"documents.{doc.get('id')}: external_refs references unknown source {ref.get('source_id')}")
            if ref.get("relation") not in EXTERNAL_RELATIONS:
                errors.append(f"documents.{doc.get('id')}: invalid external_refs relation")
    audit = plan.get("audit", {})
    if audit.get("status") not in {"pending", "passed", "failed"}:
        errors.append("audit.status must be pending, passed, or failed")
    if audit.get("verdict") not in {None, "PASS", "FAIL"}:
        errors.append("audit.verdict must be PASS, FAIL, or null")
    if audit.get("verdict") == "FAIL" and audit.get("status") != "failed":
        errors.append("audit.verdict FAIL requires audit.status failed")
    return errors


def run_prepare(repo: Path, manifest_path: str | None, output: str | None) -> int:
    """Read-only evidence/planning pack. No web access, no writes to the
    repository beyond the requested output path."""
    manifest = None
    if manifest_path:
        manifest = load_manifest(Path(manifest_path))
    plan = default_plan(repo)
    if manifest is not None:
        project = manifest.get("project", {})
        scale_rec = project.get("scale", {})
        plan["project"] = {
            "scale": scale_rec.get("class") or plan["project"]["scale"],
            "layout": scale_rec.get("layout") or plan["project"]["layout"],
            "tier": project.get("tier") or plan["project"]["tier"],
            "profiles": project.get("profiles", plan["project"]["profiles"]),
            "graph_lock": manifest.get("graph") if isinstance(manifest.get("graph"), dict) else None,
        }
    errors = validate_plan(plan)
    if errors:
        for error in errors:
            print(f"error: {error}", file=__import__("sys").stderr)
        return 1
    if output:
        Path(output).write_text(dump_json(plan), encoding="utf-8")
        print(f"Wrote architecture plan to {output}")
    else:
        print(dump_json(plan), end="")
    return 0


def run_import(repo: Path, analysis: str) -> int:
    """Validate and deterministically write the architecture ledger."""
    path = Path(analysis)
    if not path.is_file():
        return fail(f"analysis file not found: {path}", 1)
    try:
        plan = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return fail(f"invalid analysis JSON: {exc}", 1)
    errors = validate_plan(plan)
    if errors:
        for error in errors:
            print(f"error: {error}", file=__import__("sys").stderr)
        return 1
    write_plan(repo, plan)
    print(f"Imported architecture plan to {plan_path(repo)}")
    return 0


def run_decide(repo: Path, select: list[str], decline: list[str], research_policy: str) -> int:
    plan = read_plan(repo)
    if research_policy not in RESEARCH_POLICIES:
        return fail(f"research-policy must be one of: {', '.join(sorted(RESEARCH_POLICIES))}", 2)
    if plan.get("research", {}).get("policy") != "off":
        return fail("research policy is already recorded; use --research-policy to change it", 1)
    doc_by_id = {doc["id"]: doc for doc in plan.get("documents", [])}
    for doc_id in select:
        if doc_id not in doc_by_id:
            return fail(f"unknown document id: {doc_id}", 1)
        doc_by_id[doc_id]["state"] = "selected"
    for doc_id in decline:
        if doc_id not in doc_by_id:
            return fail(f"unknown document id: {doc_id}", 1)
        doc_by_id[doc_id]["state"] = "declined"
    for doc in plan.get("documents", []):
        if doc["state"] == "proposed":
            doc["state"] = "declined"
    plan["research"]["policy"] = research_policy
    plan["research"]["authorized"] = research_policy != "off"
    write_plan(repo, plan)
    selected = [doc["id"] for doc in plan["documents"] if doc["state"] == "selected"]
    print(f"Recorded {len(selected)} selected document(s); research policy: {research_policy}.")
    return 0


def run_status(repo: Path, as_json: bool) -> int:
    plan = read_plan(repo)
    selected = [doc for doc in plan.get("documents", []) if doc["state"] == "selected"]
    if as_json:
        payload = {
            "schema": SCHEMA_VERSION,
            "generated_at": plan.get("generated_at"),
            "selected_documents": selected,
            "unresolved_gaps": [
                question for question in plan.get("research", {}).get("questions", [])
                if not question.get("resolved")
            ],
            "research_policy": plan.get("research", {}).get("policy"),
            "audit": plan.get("audit", {}),
        }
        print(dump_json(payload), end="")
    else:
        print(f"Architecture plan: {plan_path(repo)}")
        print(f"Selected documents ({len(selected)}):")
        for doc in selected:
            print(f"  {doc.get('id')}  {doc.get('path')}")
        print(f"Research policy: {plan.get('research', {}).get('policy')}")
        audit = plan.get("audit", {})
        print(f"Pack audit: {audit.get('status')} ({audit.get('verdict') or 'pending'})")
    return 0


def run_validate(repo: Path) -> int:
    plan = read_plan(repo)
    errors = validate_plan(plan)
    if errors:
        for error in errors:
            print(f"error: {error}", file=__import__("sys").stderr)
        return 1
    print("architecture plan ok")
    return 0


def run_audit(repo: Path, verdict: str, report: str | None) -> int:
    plan = read_plan(repo)
    if verdict not in {"PASS", "FAIL"}:
        return fail("--verdict must be PASS or FAIL", 2)
    plan["audit"]["verdict"] = verdict
    plan["audit"]["report"] = report
    plan["audit"]["status"] = "passed" if verdict == "PASS" else "failed"
    write_plan(repo, plan)
    print(f"Recorded pack audit {verdict}.")
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
    decide.add_argument("--research-policy", required=True, choices=sorted(RESEARCH_POLICIES))
    status = sub.add_parser("status")
    status.add_argument("--repo", required=True, type=Path)
    status.add_argument("--json", action="store_true")
    validate = sub.add_parser("validate")
    validate.add_argument("--repo", required=True, type=Path)
    audit = sub.add_parser("audit")
    audit.add_argument("--repo", required=True, type=Path)
    audit.add_argument("--verdict", required=True, choices=["PASS", "FAIL"])
    audit.add_argument("--report")
    args = parser.parse_args(argv)
    try:
        if args.command == "prepare":
            return run_prepare(args.repo, args.manifest, None)
        if args.command == "import":
            return run_import(args.repo, args.analysis)
        if args.command == "decide":
            return run_decide(args.repo, args.select, args.decline, args.research_policy)
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
