#!/usr/bin/env python3
"""Query the split Docforge catalog. Agents and scripts use this — not raw files."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from runtime.common.python._util import dump_json, fail

SKILL_ROOT = Path(__file__).resolve().parent.parent.parent.parent
CATALOG_DIR = SKILL_ROOT / ".metadata" / "catalog"
INDEX_PATH = CATALOG_DIR / "index.json"
TYPES_DIR = CATALOG_DIR / "types"
PROFILES_DIR = CATALOG_DIR / "profiles"
ALLOWED_DOMINANT_FORMS = {
    None,
    "table",
    "flowchart",
    "sequenceDiagram",
    "erDiagram",
    "stateDiagram-v2",
}
TARGET_DEPTHS = {"orientation", "deep-dive", "reference", "router"}
MODEL_DEPTHS = {
    "c4": ("context", "container", "component", "component-evidence"),
    "arc42": ("context", "building-block-l1", "building-block-l2", "runtime-scenarios"),
    "stride": ("boundary-element", "full-element", "interaction-risk"),
    "adr": ("nygard", "madr-min", "madr-full"),
    "prov": ("core", "expanded", "qualified"),
    "mermaid": ("single-form", "complementary", "annotated"),
}
MODEL_DEPTH_ORDER = ("c4", "arc42", "stride", "adr", "prov", "mermaid")
CONTRACT_REVISION_RE = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")
PROFILE_DIMENSIONS = ["shapes", "platforms", "frameworks", "concerns", "audiences"]
REQUIRED_DOC_FIELDS = {
    "id",
    "type",
    "path",
    "group",
    "selection",
    "summary",
    "contract_file",
    "template_file",
    "requires",
    "target_depth",
    "write_order",
    "provenance_mode",
    "audit_profile",
}
CATALOG_VERSION = "2.11.0"


def load_index() -> dict:
    if not INDEX_PATH.is_file():
        raise ValueError(f"catalog index not found: {INDEX_PATH}")
    return json.loads(INDEX_PATH.read_text(encoding="utf-8"))


def load_profile(dimension: str) -> list:
    # Accept singular aliases from CLI: shape → shapes
    aliases = {
        "shape": "shapes",
        "platform": "platforms",
        "framework": "frameworks",
        "concern": "concerns",
        "audience": "audiences",
    }
    dimension = aliases.get(dimension, dimension)
    if dimension not in PROFILE_DIMENSIONS:
        raise ValueError(
            f"unknown profile dimension: {dimension}; "
            f"expected one of: {', '.join(PROFILE_DIMENSIONS)}"
        )
    path = PROFILES_DIR / f"{dimension}.json"
    if not path.is_file():
        raise ValueError(f"profile file not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def load_profiles() -> dict[str, list]:
    return {dimension: load_profile(dimension) for dimension in PROFILE_DIMENSIONS}


def index_row(doc_id: str) -> dict:
    index = load_index()
    row = next((r for r in index["document_types"] if r["id"] == doc_id), None)
    if row is None:
        raise ValueError(f"unknown document type id: {doc_id}")
    return row


def resolve_catalog_id(value: str) -> str:
    """Resolve a catalog id, or the unique dynamic type used by an instance."""
    index = load_index()
    if any(row["id"] == value for row in index["document_types"]):
        return value
    matches = [
        row["id"] for row in index["document_types"]
        if load_type(row["id"]).get("selection", {}).get("mode") == "dynamic"
        and load_type(row["id"]).get("type") == value
    ]
    if len(matches) == 1:
        return matches[0]
    raise ValueError(f"unknown document type id or dynamic type: {value}")


def load_type(doc_id: str) -> dict:
    row = index_row(doc_id)
    record = row.get("record", f"types/{doc_id}.json")
    path = CATALOG_DIR / record
    if not path.is_file():
        raise ValueError(f"unknown document type id: {doc_id}")
    detail = json.loads(path.read_text(encoding="utf-8"))
    return detail


def load_types(doc_ids: list[str]) -> list[dict]:
    return [load_type(doc_id) for doc_id in doc_ids]


def load_all_types() -> list[dict]:
    index = load_index()
    return [load_type(row["id"]) for row in index["document_types"]]


def as_legacy_catalog() -> dict:
    """Reconstruct the pre-split monolith shape for callers that need the full graph."""
    index = load_index()
    tiers = index["tiers"]
    if isinstance(tiers, dict):
        tier_list = [{"id": tid, "order": meta["order"]} for tid, meta in tiers.items()]
    else:
        tier_list = list(tiers)
    return {
        "$schema": "catalog-schema.json",
        "version": index["version"],
        "tiers": tier_list,
        "profiles": load_profiles(),
        "groups": index.get("groups", []),
        "capabilities": index.get("capabilities", []),
        "documents": [_legacy_document_view(detail) for detail in load_all_types()],
        "cue_hints": index.get("cue_hints", []),
    }


def tier_rows(tier: str) -> list[dict]:
    index = load_index()
    tiers = index["tiers"]
    if isinstance(tiers, dict):
        if tier not in tiers:
            raise ValueError(f"unknown tier: {tier}")
    else:
        if tier not in {item["id"] for item in tiers}:
            raise ValueError(f"unknown tier: {tier}")
    return [_legacy_index_row(row) for row in index["document_types"] if row["tier"] == tier]


# Every catalog document is materialized through the same per-document
# writing procedure, regardless of group.
ROUTE_WORKFLOW = "workflows/writing.md"
GROUP_SUMMARIES = {
    "root": "Root-level entrypoints: README, SKILL.md, and package descriptors.",
    "product": "Product surface: overview, quickstart, and audience-specific product views.",
    "architecture": "System architecture: structure, boundaries, and integration surfaces.",
    "flows": "End-to-end flow documentation derived from the flow index.",
    "engineering": "Engineering practices: conventions, testing, and tech debt.",
    "operations": "Deployment, observability, and operational runbooks.",
    "reference": "Reference lookups: APIs, configuration, and glossary.",
    "security": "Security posture, permissions, and threat model.",
    "contributing": "Contribution guidelines and root-level contributor docs.",
    "records": "Architecture decision records.",
    "portfolio": "Cross-repository portfolio layer for multi-repo diligence.",
    "agent-context": "Agent-facing context: AGENTS.md and coding-agent views.",
}


def category(group: str) -> dict:
    index = load_index()
    if group not in set(index.get("groups", [])):
        raise ValueError(f"unknown group: {group}")
    matches = []
    for row in index["document_types"]:
        detail = load_type(row["id"])
        if detail.get("group") != group:
            continue
        record = row.get("record", f"types/{row['id']}.json")
        matches.append((detail.get("write_order", 0), detail["id"], detail, record))
    matches.sort(key=lambda item: (item[0], item[1]))
    return {
        "category": group,
        "summary": GROUP_SUMMARIES.get(group, f"{group} document definitions"),
        "index": ".metadata/catalog/index.json",
        "documents": [
            {
                "id": doc_id,
                "summary": detail.get("summary"),
                "record": f".metadata/catalog/{record}",
            }
            for _, doc_id, detail, record in matches
        ],
    }


def route(value: str) -> dict:
    doc_id = resolve_catalog_id(value)
    row = index_row(doc_id)
    detail = load_type(doc_id)
    record = row.get("record", f"types/{doc_id}.json")
    model_depth = {
        model: detail["model_depth"][model]
        for model in MODEL_DEPTH_ORDER
        if model in detail.get("model_depth", {})
    }
    return {
        "id": doc_id,
        "group": detail.get("group"),
        "summary": detail.get("summary"),
        "definition": f".metadata/catalog/{record}",
        "contract": detail.get("contract_file"),
        "instruction": detail.get("instruction_file"),
        "template": detail.get("template_file"),
        "workflow": ROUTE_WORKFLOW,
        "requires": detail.get("requires", []),
        "target_depth": detail.get("target_depth"),
        "audit_profile": detail.get("audit_profile"),
        "contract_revision": detail.get("contract_revision"),
        "model_depth": model_depth,
    }


# Field order and shape of a pre-2.5 type-detail record. --id/--ids/--tier/
# --legacy must keep emitting exactly this shape; summary/contract_file/
# template_file are 2.5 additions that must not leak into those modes.
LEGACY_DOC_FIELD_ORDER = [
    "id", "type", "path", "group", "selection", "scaffold_template",
    "instruction_file", "requires", "target_depth", "write_order",
    "provenance_mode", "audit_profile", "dominant_form", "schema_min",
]


def _legacy_document_view(detail: dict) -> dict:
    view: dict = {}
    for key in LEGACY_DOC_FIELD_ORDER:
        if key == "scaffold_template":
            template_file = detail.get("template_file")
            if template_file:
                view[key] = template_file.rsplit("/", 1)[-1]
            elif "scaffold_template" in detail:
                view[key] = detail["scaffold_template"]
        elif key == "instruction_file":
            instruction_file = detail.get("instruction_file")
            view[key] = instruction_file.rsplit("/", 1)[-1] if instruction_file else None
        elif key in detail:
            view[key] = detail[key]
    return view


def _legacy_index_row(row: dict) -> dict:
    return {"id": row["id"], "tier": row["tier"], "path": row["path"]}


def merged_record(doc_id: str) -> dict:
    index = load_index()
    row = next((r for r in index["document_types"] if r["id"] == doc_id), None)
    if row is None:
        raise ValueError(f"unknown document type id: {doc_id}")
    detail = load_type(doc_id)
    view = _legacy_document_view(detail)
    return {**view, "tier": row["tier"], "index_path": row["path"]}


def _normalize_profile_ids(
    dimension: str,
    values: list[str],
    profiles: dict[str, list],
) -> list[str]:
    aliases: dict[str, str] = {}
    for definition in profiles[dimension]:
        aliases[definition["id"]] = definition["id"]
        for alias in definition.get("aliases", []):
            aliases[alias] = definition["id"]
    resolved = []
    for value in values:
        if value not in aliases:
            raise ValueError(f"unknown {dimension[:-1]}: {value}")
        canonical = aliases[value]
        if canonical not in resolved:
            resolved.append(canonical)
    return resolved


def applicable(
    *,
    shape: list[str] | None = None,
    platform: list[str] | None = None,
    framework: list[str] | None = None,
    concern: list[str] | None = None,
    audience: list[str] | None = None,
    tier: str | None = None,
    include_dynamic: bool = False,
) -> list[str]:
    """Return document-type ids applicable for the given profile/tier selection."""
    index = load_index()
    profiles = load_profiles()
    selected = {
        "shapes": _normalize_profile_ids("shapes", shape or [], profiles),
        "platforms": _normalize_profile_ids("platforms", platform or [], profiles),
        "frameworks": _normalize_profile_ids("frameworks", framework or [], profiles),
        "concerns": _normalize_profile_ids("concerns", concern or [], profiles),
        "audiences": _normalize_profile_ids("audiences", audience or [], profiles),
    }
    tiers = index["tiers"]
    if isinstance(tiers, dict):
        ranks = {tid: meta["order"] for tid, meta in tiers.items()}
    else:
        ranks = {item["id"]: item["order"] for item in tiers}
    if tier is None:
        tier = "diligence"
    if tier not in ranks:
        raise ValueError(f"unknown tier: {tier}")
    tier_rank = ranks[tier]

    ids: list[str] = []
    for row in index["document_types"]:
        detail = load_type(row["id"])
        rule = detail["selection"]
        if rule["mode"] == "dynamic" and not include_dynamic:
            continue
        if ranks[rule["min_tier"]] > tier_rank:
            continue
        selectors = rule.get("selectors", {})
        has_selectors = any(selectors.values())
        if has_selectors:
            matched = False
            for dimension, values in selectors.items():
                if dimension == "frameworks":
                    continue  # frameworks must not select documents
                selected_values = selected.get(dimension, [])
                if any(value in selected_values for value in values):
                    matched = True
                    break
            if not matched:
                continue
        ids.append(detail["id"])
    return ids


def validate() -> list[str]:
    errors: list[str] = []
    try:
        index = load_index()
    except ValueError as exc:
        return [str(exc)]
    if index.get("version") != CATALOG_VERSION:
        errors.append(f"catalog version must be {CATALOG_VERSION}, got {index.get('version')}")
    for key in ("tiers", "groups", "capabilities", "profiles", "document_types"):
        if key not in index:
            errors.append(f"index.json missing {key}")
    tiers = index.get("tiers", {})
    if isinstance(tiers, dict):
        tier_ids = set(tiers)
    else:
        tier_ids = {item["id"] for item in tiers}

    profiles: dict[str, list] = {}
    profile_ids: dict[str, set[str]] = {}
    for dimension in PROFILE_DIMENSIONS:
        path = PROFILES_DIR / f"{dimension}.json"
        if not path.is_file():
            errors.append(f"missing profile file: {path.name}")
            profiles[dimension] = []
            profile_ids[dimension] = set()
            continue
        definitions = json.loads(path.read_text(encoding="utf-8"))
        profiles[dimension] = definitions
        ids = {item.get("id") for item in definitions}
        if len(ids) != len(definitions):
            errors.append(f"{dimension}: duplicate profile id")
        profile_ids[dimension] = ids
        names: dict[str, str] = {}
        for item in definitions:
            identifier = item.get("id")
            for name in [identifier, *item.get("aliases", [])]:
                if not isinstance(name, str) or re.fullmatch(r"[a-z0-9][a-z0-9-]*", name) is None:
                    errors.append(f"{dimension}: invalid profile name {name}")
                    continue
                if name in names:
                    errors.append(
                        f"{dimension}: profile name collision {name} "
                        f"between {names[name]} and {identifier}"
                    )
                names[name] = identifier

    declared_profiles = index.get("profiles", {})
    for dimension in PROFILE_DIMENSIONS:
        rel = declared_profiles.get(dimension)
        if not rel:
            errors.append(f"index.json profiles.{dimension} is missing")
        elif not (CATALOG_DIR / rel).is_file():
            errors.append(f"index.json profiles.{dimension} points to missing file: {rel}")

    index_ids = [row["id"] for row in index.get("document_types", [])]
    if len(index_ids) != len(set(index_ids)):
        errors.append("index.json has duplicate document type ids")
    declared_records: set[Path] = set()
    for row in index.get("document_types", []):
        record = row.get("record")
        if not record:
            errors.append(f"{row['id']}: index.json entry missing record path")
            continue
        record_path = CATALOG_DIR / record
        if not record_path.is_file():
            errors.append(f"{row['id']}: record path does not resolve: {record}")
            continue
        declared_records.add(record_path.resolve())
    # Records may live flat in types/ (pre-migration) or under documents/
    # (per-group folders + flat small groups, post-migration); scan both.
    # Generated routers (index.json, README.md) are excluded, not records.
    candidate_dirs = [d for d in (TYPES_DIR, CATALOG_DIR / "documents") if d.is_dir()]
    on_disk_records: set[Path] = set()
    for base in candidate_dirs:
        for path in base.rglob("*.json"):
            if path.name == "index.json":
                continue
            on_disk_records.add(path.resolve())
    for path in sorted(on_disk_records - declared_records):
        errors.append(f"orphan record file not in index: {path.relative_to(CATALOG_DIR)}")

    groups = set(index.get("groups", []))
    capabilities = set(index.get("capabilities", []))
    static_ids: set[str] = set()
    static_paths: set[str] = set()
    dynamic_types: set[str] = set()

    for doc_id in index_ids:
        try:
            doc = load_type(doc_id)
        except ValueError as exc:
            errors.append(str(exc))
            continue
        missing = sorted(REQUIRED_DOC_FIELDS - set(doc))
        if missing:
            errors.append(f"{doc_id}: missing fields: {', '.join(missing)}")
            continue
        if doc["id"] != doc_id:
            errors.append(f"{doc_id}: id field mismatch ({doc['id']})")
        selection = doc.get("selection", {})
        if doc["group"] not in groups:
            errors.append(f"{doc_id}: unknown group {doc['group']}")
        if selection.get("min_tier") not in tier_ids:
            errors.append(f"{doc_id}: unknown tier {selection.get('min_tier')}")
        if doc.get("target_depth") not in TARGET_DEPTHS:
            errors.append(f"{doc_id}: target_depth must be one of: {', '.join(sorted(TARGET_DEPTHS))}")
        model_depth = doc.get("model_depth")
        if model_depth is not None:
            if not isinstance(model_depth, dict) or not model_depth:
                errors.append(f"{doc_id}: model_depth must be a non-empty object")
            else:
                for model, rung in model_depth.items():
                    if model not in MODEL_DEPTHS:
                        errors.append(f"{doc_id}: unknown model_depth model {model}")
                    elif rung not in MODEL_DEPTHS[model]:
                        errors.append(f"{doc_id}: invalid {model} model_depth rung {rung}")
        revision = doc.get("contract_revision")
        if revision is not None and (not isinstance(revision, str) or not CONTRACT_REVISION_RE.fullmatch(revision)):
            errors.append(f"{doc_id}: contract_revision must be MAJOR.MINOR.PATCH")
        if "selection_evidence_required" in doc and not isinstance(doc["selection_evidence_required"], bool):
            errors.append(f"{doc_id}: selection_evidence_required must be boolean")
        selectors = selection.get("selectors", {})
        if selectors.get("frameworks"):
            errors.append(f"{doc_id}: frameworks may tailor evidence but must not select documents")
        for dimension, values in selectors.items():
            if dimension not in profile_ids:
                errors.append(f"{doc_id}: unknown selector dimension {dimension}")
                continue
            for value in values:
                if value not in profile_ids[dimension]:
                    errors.append(f"{doc_id}: unknown {dimension} selector {value}")
        for requirement in doc.get("requires", []):
            if requirement not in capabilities:
                errors.append(f"{doc_id}: unknown requirement {requirement}")
        if not isinstance(doc.get("write_order"), int):
            errors.append(f"{doc_id}: write_order must be an integer")
        if doc.get("nav_order") is not None and not isinstance(doc.get("nav_order"), int):
            errors.append(f"{doc_id}: nav_order must be an integer")
        form = doc.get("dominant_form")
        if form not in ALLOWED_DOMINANT_FORMS:
            errors.append(f"{doc_id}: invalid dominant_form {form!r}")
        summary = doc.get("summary")
        if not summary or not isinstance(summary, str) or len(summary) > 160:
            errors.append(f"{doc_id}: summary must be a non-empty string of at most 160 characters")
        contract = doc.get("contract_file")
        if not contract or not (SKILL_ROOT / contract).is_file():
            errors.append(f"{doc_id}: missing contract {contract}")
        template = doc.get("template_file")
        if not template or not (SKILL_ROOT / template).is_file():
            errors.append(f"{doc_id}: missing template {template}")
        if "scaffold_template" in doc:
            errors.append(f"{doc_id}: obsolete scaffold_template field remains; use template_file")
        instruction = doc.get("instruction_file")
        if instruction and not (SKILL_ROOT / instruction).is_file():
            errors.append(f"{doc_id}: missing instruction {instruction}")
        if selection.get("mode") == "static":
            if doc["id"] in static_ids:
                errors.append(f"duplicate static id: {doc['id']}")
            if doc["path"] in static_paths:
                errors.append(f"duplicate static path: {doc['path']}")
            static_ids.add(doc["id"])
            static_paths.add(doc["path"])
        elif selection.get("mode") == "dynamic":
            if doc["type"] in dynamic_types:
                errors.append(f"duplicate dynamic type: {doc['type']}")
            dynamic_types.add(doc["type"])
            if doc["type"] in index_ids and doc["type"] != doc_id:
                errors.append(f"{doc_id}: dynamic type collides with catalog id {doc['type']}")
        else:
            errors.append(f"{doc_id}: selection.mode must be static or dynamic")

    # §0.10: infrastructure-platform must carry widened signals + aliases
    infra = next(
        (item for item in profiles.get("shapes", []) if item.get("id") == "infrastructure-platform"),
        None,
    )
    if infra is None:
        errors.append("shapes: infrastructure-platform missing")
    else:
        patterns = {s.get("pattern") for s in infra.get("signals", [])}
        for required in ("ansible.cfg", "**/kustomization.yaml", "**/playbook*.yml"):
            if required not in patterns:
                errors.append(f"infrastructure-platform missing signal pattern {required}")
        aliases = set(infra.get("aliases", []))
        for alias in ("deployment-config", "iac"):
            if alias not in aliases:
                errors.append(f"infrastructure-platform missing alias {alias}")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tier", choices=["spine", "diligence", "portfolio"])
    parser.add_argument("--id", dest="doc_id")
    parser.add_argument("--ids", help="Comma-separated document type ids")
    parser.add_argument(
        "--profile",
        help="Profile dimension: shapes|platforms|frameworks|concerns|audiences",
    )
    parser.add_argument("--applicable", action="store_true")
    parser.add_argument("--shape", action="append", default=[])
    parser.add_argument("--platform", action="append", default=[])
    parser.add_argument("--framework", action="append", default=[])
    parser.add_argument("--concern", action="append", default=[])
    parser.add_argument("--audience", action="append", default=[])
    parser.add_argument(
        "--applicable-tier",
        dest="applicable_tier",
        choices=["spine", "diligence", "portfolio"],
        default="diligence",
    )
    parser.add_argument("--include-dynamic", action="store_true")
    parser.add_argument("--legacy", action="store_true", help="Emit reconstructed monolith JSON")
    parser.add_argument("--validate", action="store_true")
    parser.add_argument("--category", dest="category", help="Group id, e.g. architecture")
    parser.add_argument("--route", dest="route_id", help="Document id to resolve")
    args = parser.parse_args(argv)

    modes = sum(
        bool(x)
        for x in (
            args.tier,
            args.doc_id,
            args.ids,
            args.profile,
            args.applicable,
            args.validate,
            args.legacy,
            args.category,
            args.route_id,
        )
    )
    if modes != 1:
        return fail(
            "specify exactly one of --tier, --id, --ids, --profile, "
            "--applicable, --legacy, --validate, --category, --route",
            2,
        )

    try:
        if args.validate:
            errors = validate()
            if errors:
                for error in errors:
                    print(f"error: {error}", file=sys.stderr)
                print(f"{len(errors)} validation error(s)", file=sys.stderr)
                return 1
            print("catalog ok")
            return 0
        if args.legacy:
            print(dump_json(as_legacy_catalog()), end="")
            return 0
        if args.tier:
            print(dump_json(tier_rows(args.tier)), end="")
            return 0
        if args.doc_id:
            print(dump_json(merged_record(args.doc_id)), end="")
            return 0
        if args.ids:
            ids = [part.strip() for part in args.ids.split(",") if part.strip()]
            print(dump_json([merged_record(doc_id) for doc_id in ids]), end="")
            return 0
        if args.profile:
            print(dump_json(load_profile(args.profile)), end="")
            return 0
        if args.applicable:
            ids = applicable(
                shape=args.shape,
                platform=args.platform,
                framework=args.framework,
                concern=args.concern,
                audience=args.audience,
                tier=args.applicable_tier,
                include_dynamic=args.include_dynamic,
            )
            print(dump_json(ids), end="")
            return 0
        if args.category:
            print(dump_json(category(args.category)), end="")
            return 0
        if args.route_id:
            print(dump_json(route(args.route_id)), end="")
            return 0
    except ValueError as exc:
        return fail(str(exc), 2)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
