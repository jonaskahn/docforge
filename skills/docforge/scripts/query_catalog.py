#!/usr/bin/env python3
"""Query the split Docforge catalog. Agents and scripts use this — not raw files."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from _util import dump_json, fail

SKILL_ROOT = Path(__file__).resolve().parent.parent
CATALOG_DIR = SKILL_ROOT / ".metadata" / "catalog"
INDEX_PATH = CATALOG_DIR / "index.json"
TYPES_DIR = CATALOG_DIR / "types"
PROFILES_DIR = CATALOG_DIR / "profiles"
CONTRACTS_DIR = SKILL_ROOT / "references" / "catalog-contracts"
ALLOWED_DOMINANT_FORMS = {
    None,
    "table",
    "flowchart",
    "sequenceDiagram",
    "erDiagram",
}
PROFILE_DIMENSIONS = ["shapes", "platforms", "frameworks", "concerns", "audiences"]
REQUIRED_DOC_FIELDS = {
    "id",
    "type",
    "path",
    "group",
    "selection",
    "scaffold_template",
    "requires",
    "target_depth",
    "write_order",
    "provenance_mode",
    "audit_profile",
}


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


def load_type(doc_id: str) -> dict:
    path = TYPES_DIR / f"{doc_id}.json"
    if not path.is_file():
        raise ValueError(f"unknown document type id: {doc_id}")
    return json.loads(path.read_text(encoding="utf-8"))


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
        "documents": load_all_types(),
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
    return [row for row in index["document_types"] if row["tier"] == tier]


def merged_record(doc_id: str) -> dict:
    index = load_index()
    row = next((r for r in index["document_types"] if r["id"] == doc_id), None)
    if row is None:
        raise ValueError(f"unknown document type id: {doc_id}")
    detail = load_type(doc_id)
    return {**detail, "tier": row["tier"], "index_path": row["path"]}


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
    if index.get("version") != "2.4.0":
        errors.append(f"catalog version must be 2.4.0, got {index.get('version')}")
    for key in ("tiers", "groups", "capabilities", "document_types"):
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

    index_ids = [row["id"] for row in index.get("document_types", [])]
    if len(index_ids) != len(set(index_ids)):
        errors.append("index.json has duplicate document type ids")
    type_files = {path.stem for path in TYPES_DIR.glob("*.json")}
    for doc_id in index_ids:
        if doc_id not in type_files:
            errors.append(f"index references missing type file: {doc_id}.json")
    for stem in sorted(type_files):
        if stem not in index_ids:
            errors.append(f"orphan type file not in index: {stem}.json")

    groups = set(index.get("groups", []))
    capabilities = set(index.get("capabilities", []))
    static_ids: set[str] = set()
    static_paths: set[str] = set()
    dynamic_types: set[str] = set()
    contract_types: set[str] = set()
    if CONTRACTS_DIR.is_dir():
        contract_types = {
            path.stem for path in CONTRACTS_DIR.glob("*.md") if path.name != "README.md"
        }

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
        form = doc.get("dominant_form")
        if form not in ALLOWED_DOMINANT_FORMS:
            errors.append(f"{doc_id}: invalid dominant_form {form!r}")
        if contract_types and doc["type"] not in contract_types:
            errors.append(f"{doc_id}: document type missing from catalog-contracts/")
        template = SKILL_ROOT / "assets" / "templates" / doc["scaffold_template"]
        if not template.is_file():
            errors.append(f"{doc_id}: missing template {doc['scaffold_template']}")
        instruction = doc.get("instruction_file")
        if instruction and not (SKILL_ROOT / "instructions" / instruction).is_file():
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
        )
    )
    if modes != 1:
        return fail(
            "specify exactly one of --tier, --id, --ids, --profile, "
            "--applicable, --legacy, --validate",
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
    except ValueError as exc:
        return fail(str(exc), 2)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
