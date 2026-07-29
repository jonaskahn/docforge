#!/usr/bin/env python3
"""Create and maintain a Docforge 2.0 manifest from the canonical catalog."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

from detect_profiles import detect as detect_profiles
from provenance_frontmatter import GENERATOR_VERSION, scaffold_provenance

SKILL_ROOT = Path(__file__).resolve().parent.parent
CATALOG_PATH = SKILL_ROOT / ".metadata" / "catalog.json"
MANIFEST_REL = Path(".docforge/manifest.json")
FLOW_INDEX_REL = Path(".docforge/flow-index.json")
STATUSES = ["planned", "in_progress", "generated", "needs_review", "complete", "skipped"]
TRANSITIONS = {
    "planned": {"in_progress", "skipped"},
    "in_progress": {"generated", "needs_review", "skipped"},
    "generated": {"needs_review", "complete", "skipped"},
    "needs_review": {"in_progress", "skipped"},
    "complete": {"in_progress"},
    "skipped": {"planned"},
}
TOOL_VERSION = GENERATOR_VERSION
MANIFEST_VERSION = "3.1"


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
    if data.get("version") != MANIFEST_VERSION:
        raise ValueError(
            f"manifest must use version {MANIFEST_VERSION}: {path}; "
            "run migrate_metadata.py for 3.0, or replace unsupported older manifests"
        )
    return data


def flow_is_main_priority(row: dict) -> bool:
    if row.get("priority") == "main":
        return True
    if row.get("priority") == "deferred":
        return False
    return row.get("status") in {"main", "documented"}


def load_main_flow(repo: Path, doc_id: str, doc_path: str) -> tuple[dict, dict]:
    path = repo / FLOW_INDEX_REL
    if not path.is_file():
        raise ValueError(
            f"flow index not found: {path}; run flow_index.py harvest before adding flow documents"
        )
    try:
        index = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError(f"invalid flow index: {path}: {error}") from error
    slug = PurePosixPath(doc_path).stem
    row = next(
        (
            item for item in index.get("flows", [])
            if item.get("id") == doc_id or item.get("slug") == slug
        ),
        None,
    )
    if row is None:
        raise ValueError(f"flow is not present in {FLOW_INDEX_REL}: {doc_id}")
    status = row.get("status", "unranked")
    if status in {"main", "documented"}:
        return index, row
    if status == "placeholder" and flow_is_main_priority(row):
        return index, row
    raise ValueError(
        f"flow {doc_id} is {status}; only main-priority flows become documents"
    )


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
        "provenance": scaffold_provenance(
            definition["id"],
            definition["path"],
            target_depth=definition["target_depth"],
        ),
        "audit": None,
    }


PROFILE_DIMENSIONS = ["shapes", "platforms", "frameworks", "concerns", "audiences"]
ORIGIN_KINDS = {
    "shapes": "shape",
    "platforms": "platform",
    "frameworks": "framework",
    "concerns": "concern",
    "audiences": "audience",
}


def normalize_profiles(catalog: dict, raw: dict[str, list[str]]) -> dict[str, list[str]]:
    normalized: dict[str, list[str]] = {}
    for dimension in PROFILE_DIMENSIONS:
        definitions = catalog["profiles"][dimension]
        aliases: dict[str, str] = {}
        for definition in definitions:
            aliases[definition["id"]] = definition["id"]
            aliases.update({alias: definition["id"] for alias in definition.get("aliases", [])})
        unknown = [value for value in raw.get(dimension, []) if value not in aliases]
        if unknown:
            singular = dimension[:-1] if dimension != "audiences" else "audience"
            expected = ", ".join(item["id"] for item in definitions)
            raise ValueError(f"unknown {singular}: {unknown[0]}; expected one of: {expected}")
        requested = {aliases[value] for value in raw.get(dimension, [])}
        normalized[dimension] = [
            definition["id"] for definition in definitions
            if definition["id"] in requested
        ]
    return normalized


def matching_origins(rule: dict, profiles: dict[str, list[str]]) -> list[dict]:
    origins: list[dict] = []
    for dimension in PROFILE_DIMENSIONS:
        selected = profiles.get(dimension, [])
        accepted = rule.get("selectors", {}).get(dimension, [])
        origins.extend(
            {"kind": ORIGIN_KINDS[dimension], "id": value}
            for value in selected if value in accepted
        )
    return origins


def add_ancestor_indexes(catalog: dict, selected: list[dict]) -> None:
    definitions = {
        item["path"]: item for item in catalog["documents"]
        if item["selection"]["mode"] == "static" and item["type"] in {
            "folder-index", "docs-index", "portfolio-index",
            "decision-index", "portfolio-decisions-index", "flow-index",
        }
    }
    selected_paths = {item["path"] for item in selected}
    changed = True
    while changed:
        changed = False
        for child in list(selected):
            path = PurePosixPath(child["path"])
            parent = path.parent
            while str(parent) not in (".", ""):
                candidate = str(parent / "README.md")
                definition = definitions.get(candidate)
                if definition and candidate not in selected_paths:
                    selected.append(make_document(
                        definition,
                        [{"kind": "ancestor", "id": child["id"]}],
                    ))
                    selected_paths.add(candidate)
                    changed = True
                parent = parent.parent


def selected_static_documents(
    catalog: dict,
    repo: Path,
    tier: str,
    profiles: dict[str, list[str]],
) -> list[dict]:
    ranks = {item["id"]: item["order"] for item in catalog["tiers"]}
    selected: list[dict] = []
    for definition in catalog["documents"]:
        rule = definition["selection"]
        if rule["mode"] != "static":
            continue
        tier_selected = ranks[rule["min_tier"]] <= ranks[tier]
        if not tier_selected:
            continue
        origins = matching_origins(rule, profiles)
        has_selectors = any(rule.get("selectors", {}).values())
        if has_selectors and not origins:
            continue
        evidence = condition_evidence(repo, rule.get("condition"))
        if rule.get("condition") and not evidence:
            continue
        if not has_selectors:
            origins.append({"kind": "tier", "id": rule["min_tier"]})
        if rule.get("condition"):
            origins.append({"kind": "condition", "id": rule["condition"]})
        selected.append(make_document(definition, origins, evidence))
    add_ancestor_indexes(catalog, selected)
    return sorted(selected, key=lambda item: (item["write_order"], item["path"], item["id"]))


def cmd_init(args: argparse.Namespace) -> int:
    if args.obsolete_overlay:
        return fail(
            "--overlay is unsupported in Docforge 2.0; use --shape, --platform, "
            "--framework, --concern, or --audience",
            2,
        )
    path = manifest_path(args.repo)
    if path.exists() and not args.force:
        return fail(f"manifest already exists: {path}; pass --force to replace it")
    catalog = load_catalog()
    try:
        profiles = normalize_profiles(catalog, {
            "shapes": args.shape,
            "platforms": args.platform,
            "frameworks": args.framework,
            "concerns": args.concern,
            "audiences": args.audience or ["engineers", "beginners"],
        })
    except ValueError as exc:
        return fail(str(exc), 2)
    docs = selected_static_documents(catalog, args.repo, args.tier, profiles)
    manifest = {
        "version": MANIFEST_VERSION,
        "generated_at": now_iso(),
        "project": {
            "name": args.name or args.repo.resolve().name,
            "root": str(args.repo.resolve()),
            "tier": args.tier,
            "profiles": profiles,
        },
        "discovery": detect_profiles(args.repo),
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
    flow_index = None
    flow_row = None
    try:
        manifest = load_manifest(args.repo)
        catalog = load_catalog()
        definition = dynamic_definition(catalog, args.type)
        validate_relative_path(args.path)
        if args.type == "flow":
            flow_index, flow_row = load_main_flow(args.repo, args.id, args.path)
    except ValueError as exc:
        return fail(str(exc), 2)
    ranks = {item["id"]: item["order"] for item in catalog["tiers"]}
    rule = definition["selection"]
    if ranks[rule["min_tier"]] > ranks[manifest["project"]["tier"]]:
        return fail(f"dynamic type {args.type} requires tier {rule['min_tier']}", 2)
    required_selectors = rule.get("selectors", {})
    profile_origins: list[dict] = []
    if any(required_selectors.values()):
        profile_origins = matching_origins(rule, manifest["project"]["profiles"])
        if not profile_origins:
            requirements = ", ".join(
                f"{ORIGIN_KINDS[dimension]}: {', '.join(values)}"
                for dimension, values in required_selectors.items() if values
            )
            return fail(f"dynamic type {args.type} requires profile {requirements}", 2)
    evidence = condition_evidence(args.repo, rule.get("condition"))
    if flow_row is not None:
        evidence = [str(FLOW_INDEX_REL), *[
            str(item.get("artifact"))
            for item in flow_row.get("evidence", [])
            if item.get("artifact")
        ]]
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
    origins = [{"kind": "dynamic", "id": definition["type"]}, *profile_origins]
    if rule.get("condition"):
        origins.append({"kind": "condition", "id": rule["condition"]})
    doc = make_document(actual, origins, evidence)
    manifest["documents"].append(doc)
    manifest["documents"].sort(key=lambda item: (item["write_order"], item["path"], item["id"]))
    save_manifest(args.repo, manifest)
    if flow_index is not None and flow_row is not None:
        flow_row["status"] = "documented"
        (args.repo / FLOW_INDEX_REL).write_text(dump_json(flow_index), encoding="utf-8")
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
    print(f"repo: {project['name']}  tier: {project['tier']}")
    for dimension in PROFILE_DIMENSIONS:
        values = ", ".join(project["profiles"][dimension]) or "none"
        print(f"  {dimension}: {values}")
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
    init.add_argument("--shape", action="append", default=[])
    init.add_argument("--platform", action="append", default=[])
    init.add_argument("--framework", action="append", default=[])
    init.add_argument("--concern", action="append", default=[])
    init.add_argument("--audience", action="append", default=[])
    init.add_argument("--overlay", dest="obsolete_overlay", action="append", default=[], help=argparse.SUPPRESS)
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
