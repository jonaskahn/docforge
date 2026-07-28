#!/usr/bin/env python3
"""Create and maintain a Docforge 2.0 manifest from the canonical catalog."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

SKILL_ROOT = Path(__file__).resolve().parent.parent
CATALOG_PATH = SKILL_ROOT / ".metadata" / "catalog.json"
MANIFEST_REL = Path(".docforge/manifest.json")
STATUSES = ["planned", "in_progress", "generated", "needs_review", "complete", "skipped"]
TRANSITIONS = {
    "planned": {"in_progress", "skipped"},
    "in_progress": {"generated", "needs_review", "skipped"},
    "generated": {"needs_review", "complete", "skipped"},
    "needs_review": {"in_progress", "skipped"},
    "complete": {"in_progress"},
    "skipped": {"planned"},
}


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def dump_json(value: dict) -> str:
    return json.dumps(value, indent=2, ensure_ascii=False) + "\n"


def fail(message: str, code: int = 1) -> int:
    print(f"error: {message}", file=sys.stderr)
    return code


def load_catalog() -> dict:
    return json.loads(CATALOG_PATH.read_text(encoding="utf-8"))


def manifest_path(repo: Path) -> Path:
    return repo / MANIFEST_REL


def load_manifest(repo: Path) -> dict:
    path = manifest_path(repo)
    if not path.is_file():
        raise ValueError(f"manifest not found: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("version") != "2.0":
        raise ValueError(f"manifest version must be 2.0: {path}")
    return data


def save_manifest(repo: Path, manifest: dict) -> None:
    docs = manifest["documents"]
    manifest["metadata"] = {
        "total_documents": len(docs),
        "planned": sum(d["status"] == "planned" for d in docs),
        "in_progress": sum(d["status"] == "in_progress" for d in docs),
        "generated": sum(d["status"] == "generated" for d in docs),
        "needs_review": sum(d["status"] == "needs_review" for d in docs),
        "complete": sum(d["status"] == "complete" for d in docs),
        "skipped": sum(d["status"] == "skipped" for d in docs),
        "last_updated": now_iso(),
    }
    path = manifest_path(repo)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dump_json(manifest), encoding="utf-8")


def condition_evidence(repo: Path, condition: str | None) -> list[str]:
    if condition is None:
        return []
    if condition == "conventions_source":
        candidates = [
            "CONVENTIONS.md", "docs/CONVENTIONS.md", "docs/conventions.md",
            ".editorconfig", "STYLEGUIDE.md",
        ]
    elif condition == "ticket_evidence":
        candidates = [
            ".docforge/tickets.json", "tickets.json", "backlog.json",
            "BACKLOG.md", "docs/backlog.md", ".github/ISSUE_TEMPLATE",
        ]
    else:
        return []
    return [candidate for candidate in candidates if (repo / candidate).exists()]


def validate_relative_path(value: str) -> None:
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or value in ("", "."):
        raise ValueError(f"path must be a safe repository-relative path: {value}")


def make_document(definition: dict, origins: list[dict], evidence: list[str] | None = None) -> dict:
    return {
        "id": definition["id"],
        "type": definition["type"],
        "path": definition["path"],
        "group": definition["group"],
        "selection": {
            "origins": origins,
            "evidence": evidence or [],
        },
        "status": "planned",
        "requires": list(definition["requires"]),
        "scaffold_template": definition["scaffold_template"],
        "instruction_file": definition.get("instruction_file"),
        "target_depth": definition["target_depth"],
        "write_order": definition["write_order"],
        "provenance_mode": definition["provenance_mode"],
        "audit_profile": definition["audit_profile"],
        "provenance": {"sections": []},
        "audit": None,
    }


def selected_static_documents(catalog: dict, repo: Path, tier: str, overlays: list[str]) -> list[dict]:
    ranks = {item["id"]: item["order"] for item in catalog["tiers"]}
    selected: list[dict] = []
    for definition in catalog["documents"]:
        rule = definition["selection"]
        if rule["mode"] != "static":
            continue
        tier_selected = ranks[rule["min_tier"]] <= ranks[tier]
        matching_overlays = [overlay for overlay in overlays if overlay in rule["overlays"]]
        trigger_overlays = [
            overlay for overlay in overlays
            if overlay in rule.get("include_if_overlay", [])
        ]
        if rule["overlays"] and (not tier_selected or not matching_overlays):
            continue
        if not rule["overlays"] and not tier_selected and not trigger_overlays:
            continue
        evidence = condition_evidence(repo, rule.get("condition"))
        if rule.get("condition") and not evidence:
            continue
        origins = []
        if not rule["overlays"] and tier_selected:
            origins.append({"kind": "tier", "id": rule["min_tier"]})
        origins.extend({"kind": "overlay", "id": overlay} for overlay in matching_overlays)
        origins.extend({"kind": "overlay", "id": overlay} for overlay in trigger_overlays)
        if rule.get("condition"):
            origins.append({"kind": "condition", "id": rule["condition"]})
        selected.append(make_document(definition, origins, evidence))
    return sorted(selected, key=lambda item: (item["write_order"], item["path"], item["id"]))


def cmd_init(args: argparse.Namespace) -> int:
    path = manifest_path(args.repo)
    if path.exists() and not args.force:
        return fail(f"manifest already exists: {path}; pass --force to replace it")
    catalog = load_catalog()
    overlay_ids = [item["id"] for item in catalog["overlays"]]
    unknown = [item for item in args.overlay if item not in overlay_ids]
    if unknown:
        return fail(f"unknown overlay: {unknown[0]}; expected one of: {', '.join(overlay_ids)}", 2)
    overlays = [item for item in overlay_ids if item in set(args.overlay)]
    docs = selected_static_documents(catalog, args.repo, args.tier, overlays)
    manifest = {
        "version": "2.0",
        "generated_at": now_iso(),
        "project": {
            "name": args.name or args.repo.resolve().name,
            "root": str(args.repo.resolve()),
            "tier": args.tier,
            "overlays": overlays,
        },
        "documents": docs,
        "metadata": {},
    }
    save_manifest(args.repo, manifest)
    print(f"Wrote {path} — tier {args.tier}, {len(docs)} static documents planned.")
    return 0


def dynamic_definition(catalog: dict, type_name: str) -> dict:
    matches = [
        item for item in catalog["documents"]
        if item["selection"]["mode"] == "dynamic" and item["type"] == type_name
    ]
    if not matches:
        valid = sorted({
            item["type"] for item in catalog["documents"]
            if item["selection"]["mode"] == "dynamic"
        })
        raise ValueError(f"unknown dynamic type: {type_name}; expected one of: {', '.join(valid)}")
    return matches[0]


def path_matches(pattern: str, actual: str) -> bool:
    expression = "^" + re.escape(pattern).replace(r"\{slug\}", r"[a-z0-9][a-z0-9-]*") + "$"
    return re.fullmatch(expression, actual) is not None


def cmd_add(args: argparse.Namespace) -> int:
    try:
        manifest = load_manifest(args.repo)
        catalog = load_catalog()
        definition = dynamic_definition(catalog, args.type)
        validate_relative_path(args.path)
    except ValueError as exc:
        return fail(str(exc), 2)
    ranks = {item["id"]: item["order"] for item in catalog["tiers"]}
    rule = definition["selection"]
    if ranks[rule["min_tier"]] > ranks[manifest["project"]["tier"]]:
        return fail(f"dynamic type {args.type} requires tier {rule['min_tier']}", 2)
    if rule["overlays"] and not set(rule["overlays"]) & set(manifest["project"]["overlays"]):
        return fail(f"dynamic type {args.type} requires overlay: {', '.join(rule['overlays'])}", 2)
    evidence = condition_evidence(args.repo, rule.get("condition"))
    if rule.get("condition") == "ticket_evidence" and not evidence:
        return fail(f"dynamic type {args.type} requires ticket evidence in the repository", 2)
    if not path_matches(definition["path"], args.path):
        return fail(f"path '{args.path}' does not match catalog pattern '{definition['path']}'", 2)
    if re.fullmatch(r"[a-z0-9][a-z0-9_-]*", args.id) is None:
        return fail(f"document id must use lowercase letters, digits, hyphens, or underscores: {args.id}", 2)
    if any(doc["id"] == args.id for doc in manifest["documents"]):
        return fail(f"document id already exists: {args.id}", 2)
    if any(doc["path"] == args.path for doc in manifest["documents"]):
        return fail(f"document path already exists: {args.path}", 2)
    actual = dict(definition)
    actual["id"] = args.id
    actual["path"] = args.path
    origins = [{"kind": "dynamic", "id": definition["type"]}]
    if rule.get("condition"):
        origins.append({"kind": "condition", "id": rule["condition"]})
    doc = make_document(actual, origins, evidence)
    manifest["documents"].append(doc)
    manifest["documents"].sort(key=lambda item: (item["write_order"], item["path"], item["id"]))
    save_manifest(args.repo, manifest)
    print(f"Added {args.id} ({args.path}) as dynamic type {args.type}.")
    return 0


def find_document(manifest: dict, doc_id: str) -> dict:
    for doc in manifest["documents"]:
        if doc["id"] == doc_id:
            return doc
    raise ValueError(f"document id not found: {doc_id}")


def cmd_set(args: argparse.Namespace) -> int:
    try:
        manifest = load_manifest(args.repo)
        doc = find_document(manifest, args.id)
    except ValueError as exc:
        return fail(str(exc), 2)
    old = doc["status"]
    if args.status == old:
        print(f"{args.id}: {old} -> {args.status}")
        return 0
    if args.status not in TRANSITIONS[old]:
        return fail(f"invalid status transition for {args.id}: {old} -> {args.status}", 2)
    if args.status == "complete":
        audit = doc.get("audit")
        if not audit or audit.get("verdict") != "PASS":
            return fail(f"{args.id} cannot be complete without a passing independent audit", 2)
    if args.status in {"planned", "in_progress"}:
        doc["audit"] = None
    doc["status"] = args.status
    save_manifest(args.repo, manifest)
    print(f"{args.id}: {old} -> {args.status}")
    return 0


def cmd_audit(args: argparse.Namespace) -> int:
    try:
        manifest = load_manifest(args.repo)
        doc = find_document(manifest, args.id)
    except ValueError as exc:
        return fail(str(exc), 2)
    if doc["status"] != "generated":
        return fail(f"{args.id} must be generated before audit", 2)
    report = args.report
    validate_relative_path(report)
    doc["audit"] = {
        "mode": args.mode,
        "verdict": args.verdict,
        "timestamp": now_iso(),
        "report_path": report,
    }
    if args.verdict == "FAIL":
        doc["status"] = "needs_review"
    save_manifest(args.repo, manifest)
    print(f"Audit {args.id}: {args.verdict} ({args.mode}) -> {report}")
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    try:
        manifest = load_manifest(args.repo)
    except ValueError as exc:
        return fail(str(exc), 2)
    project = manifest["project"]
    overlays = ", ".join(project["overlays"]) or "none"
    print(f"repo: {project['name']}  tier: {project['tier']}  overlays: {overlays}")
    print()
    for doc in manifest["documents"]:
        verdict = doc["audit"]["verdict"] if doc.get("audit") else "-"
        print(f"  {doc['status']:<12}  {verdict:<4}  {doc['id']:<28}  {doc['path']}")
    counts = manifest["metadata"]
    print()
    print(
        f"{counts['total_documents']} documents: "
        f"planned={counts['planned']} in_progress={counts['in_progress']} "
        f"generated={counts['generated']} needs_review={counts['needs_review']} "
        f"complete={counts['complete']} skipped={counts['skipped']}"
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    def add_repo(command: argparse.ArgumentParser) -> None:
        command.add_argument("--repo", required=True, type=Path)

    init = sub.add_parser("init")
    add_repo(init)
    init.add_argument("--tier", required=True, choices=["spine", "diligence", "portfolio"])
    init.add_argument("--overlay", action="append", default=[])
    init.add_argument("--name")
    init.add_argument("--force", action="store_true")
    init.set_defaults(func=cmd_init)

    add = sub.add_parser("add")
    add_repo(add)
    add.add_argument("--type", required=True)
    add.add_argument("--id", required=True)
    add.add_argument("--path", required=True)
    add.set_defaults(func=cmd_add)

    set_status = sub.add_parser("set")
    add_repo(set_status)
    set_status.add_argument("--id", required=True)
    set_status.add_argument("--status", required=True, choices=STATUSES)
    set_status.set_defaults(func=cmd_set)

    audit = sub.add_parser("audit")
    add_repo(audit)
    audit.add_argument("--id", required=True)
    audit.add_argument("--mode", required=True, choices=["subagent", "cold-pass"])
    audit.add_argument("--verdict", required=True, choices=["PASS", "FAIL"])
    audit.add_argument("--report", required=True)
    audit.set_defaults(func=cmd_audit)

    status = sub.add_parser("status")
    add_repo(status)
    status.set_defaults(func=cmd_status)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if not args.repo.is_dir():
        return fail(f"not a directory: {args.repo}", 2)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
