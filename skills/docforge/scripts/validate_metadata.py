#!/usr/bin/env python3
"""Validate the Docforge catalog, schemas, templates, peers, and release metadata."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from provenance_frontmatter import PROVENANCE_FIELDS, SCHEMA_VERSION, parse_frontmatter

SKILL_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = SKILL_ROOT.parent.parent
REQUIRED_DOC_FIELDS = {
    "id", "type", "path", "group", "selection", "scaffold_template",
    "requires", "target_depth", "write_order", "provenance_mode", "audit_profile",
}
MARKDOWN_EXCEPTIONS = {"agents-kernel.md", "claude-md.md", "claude-local-md.md"}
PUBLIC_CONTRACTS = {
    "manage_manifest": ["init", "add", "set", "status", "audit", "--repo", "--tier", "--shape", "--platform", "--framework", "--concern", "--audience", "--type", "--id", "--path", "--status", "--mode", "--verdict", "--report"],
    "detect_profiles": ["--repo", "--json", "confirmed", "candidate"],
    "scaffold_docs": ["--repo", "--manifest", "--dry-run", "--document", "--audit"],
    "precheck_graph": ["--repo", "--need", "code", "flow"],
    "check_staleness": ["--manifest", "--section", "--json", "--sync-provenance"],
    "flow_index": ["harvest", "revise", "render", "organize", "emit", "apply", "--repo", "--gitnexus-export", "--main-limit", "--output", "--organization"],
    "migrate_metadata": ["--repo", "--manifest", "--dry-run", "--report"],
}


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def validate() -> list[str]:
    errors: list[str] = []
    metadata = SKILL_ROOT / ".metadata"
    catalog = read_json(metadata / "catalog.json")
    catalog_schema = read_json(metadata / "catalog-schema.json")
    manifest_schema = read_json(metadata / "manifest-schema.json")
    flow_index_schema = read_json(metadata / "flow-index-schema.json")
    provenance_schema_path = metadata / "provenance-schema.json"
    if not provenance_schema_path.is_file():
        errors.append("provenance-schema.json is missing")
    else:
        provenance_schema = read_json(provenance_schema_path)
        if provenance_schema.get("properties", {}).get("schema", {}).get("const") != SCHEMA_VERSION:
            errors.append("provenance schema must require schema 2.0")
    if catalog.get("version") != "2.1.0":
        errors.append("catalog version must be 2.1.0")
    if catalog_schema.get("properties", {}).get("version", {}).get("const") != "2.1.0":
        errors.append("catalog schema version disagrees with catalog")
    if manifest_schema.get("properties", {}).get("version", {}).get("const") != "3.1":
        errors.append("manifest schema must require version 3.1")
    if flow_index_schema.get("properties", {}).get("version", {}).get("const") != "1.1":
        errors.append("flow index schema must require version 1.1")
    flow_item = (
        flow_index_schema.get("properties", {})
        .get("flows", {})
        .get("items", {})
        .get("properties", {})
    )
    for field in ("display_name", "family", "doc_role", "composed_into", "doc_path"):
        if field not in flow_item:
            errors.append(f"flow index schema must define flow.{field}")
    if flow_item.get("doc_role", {}).get("enum") != ["standalone", "member", "index_only"]:
        errors.append("flow index schema doc_role must be standalone|member|index_only")
    tiers = {item["id"] for item in catalog.get("tiers", [])}
    dimensions = ["shapes", "platforms", "frameworks", "concerns", "audiences"]
    profiles = catalog.get("profiles", {})
    schema_profile_required = set(
        catalog_schema.get("properties", {}).get("profiles", {}).get("required", [])
    )
    manifest_profile_required = set(
        manifest_schema.get("properties", {})
        .get("project", {}).get("properties", {})
        .get("profiles", {}).get("required", [])
    )
    if schema_profile_required != set(dimensions):
        errors.append("catalog schema profile dimensions disagree with catalog")
    if manifest_profile_required != set(dimensions):
        errors.append("manifest schema profile dimensions disagree with catalog")
    profile_ids: dict[str, set[str]] = {}
    for dimension in dimensions:
        definitions = profiles.get(dimension, [])
        if not definitions:
            errors.append(f"{dimension}: profile registry must not be empty")
        ids = {item.get("id") for item in definitions}
        if len(ids) != len(definitions):
            errors.append(f"{dimension}: duplicate profile id")
        orders = [item.get("order") for item in definitions]
        if len(set(orders)) != len(orders) or not all(isinstance(item, int) for item in orders):
            errors.append(f"{dimension}: profile order values must be unique integers")
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
            for signal in item.get("signals", []):
                kind = signal.get("kind")
                if kind not in {"path", "content", "dependency"}:
                    errors.append(f"{dimension}/{identifier}: invalid signal kind")
                if kind in {"path", "content"} and (
                    not isinstance(signal.get("pattern"), str) or not signal.get("pattern")
                ):
                    errors.append(f"{dimension}/{identifier}: signal needs a pattern")
                if kind == "content" and not signal.get("contains"):
                    errors.append(f"{dimension}/{identifier}: content signal needs contains")
                if kind == "dependency" and (
                    not signal.get("ecosystem") or not signal.get("name")
                ):
                    errors.append(f"{dimension}/{identifier}: dependency signal needs ecosystem and name")
    groups = set(catalog.get("groups", []))
    capabilities = set(catalog.get("capabilities", []))
    static_ids: set[str] = set()
    static_paths: set[str] = set()
    dynamic_types: set[str] = set()
    catalog_contract = (
        SKILL_ROOT / "references" / "document-catalog.md"
    ).read_text(encoding="utf-8")
    for index, doc in enumerate(catalog.get("documents", [])):
        label = doc.get("id", f"document[{index}]")
        missing = sorted(REQUIRED_DOC_FIELDS - set(doc))
        if missing:
            errors.append(f"{label}: missing fields: {', '.join(missing)}")
            continue
        selection = doc.get("selection", {})
        obsolete = {"overlays", "include_if_overlay"} & set(selection)
        if obsolete:
            errors.append(f"{label}: obsolete selection fields: {', '.join(sorted(obsolete))}")
        if doc["group"] not in groups:
            errors.append(f"{label}: unknown group {doc['group']}")
        if selection.get("min_tier") not in tiers:
            errors.append(f"{label}: unknown tier {selection.get('min_tier')}")
        selectors = selection.get("selectors", {})
        if "frameworks" in selectors and selectors["frameworks"]:
            errors.append(f"{label}: frameworks may tailor evidence but must not select documents")
        for dimension, values in selectors.items():
            if dimension not in profile_ids:
                errors.append(f"{label}: unknown selector dimension {dimension}")
                continue
            for value in values:
                if value not in profile_ids[dimension]:
                    errors.append(f"{label}: unknown {dimension} selector {value}")
        for requirement in doc.get("requires", []):
            if requirement not in capabilities:
                errors.append(f"{label}: unknown requirement {requirement}")
        if not isinstance(doc.get("write_order"), int):
            errors.append(f"{label}: write_order must be an integer")
        if doc["type"] not in catalog_contract:
            errors.append(f"{label}: document type is missing from document-catalog.md")
        template = SKILL_ROOT / "assets" / "templates" / doc["scaffold_template"]
        if not template.is_file():
            errors.append(f"{label}: missing template {doc['scaffold_template']}")
        instruction = doc.get("instruction_file")
        if instruction and not (SKILL_ROOT / "instructions" / instruction).is_file():
            errors.append(f"{label}: missing instruction {instruction}")
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
            errors.append(f"{label}: selection.mode must be static or dynamic")
    for template in sorted((SKILL_ROOT / "assets" / "templates").glob("*.md")):
        if template.name in MARKDOWN_EXCEPTIONS:
            continue
        text = template.read_text(encoding="utf-8")
        if not text.startswith("---\ndocforge_provenance:\n"):
            errors.append(f"{template.name}: provenance frontmatter must be YAML docforge_provenance at byte one")
            continue
        state, provenance, _ = parse_frontmatter(text)
        if state != "ok":
            errors.append(f"{template.name}: provenance frontmatter state is {state}")
            continue
        if not isinstance(provenance, dict):
            errors.append(f"{template.name}: provenance frontmatter is not valid YAML")
            continue
        missing = sorted(PROVENANCE_FIELDS - set(provenance))
        graph = provenance.get("graph")
        generator = provenance.get("generator")
        if missing or not isinstance(graph, dict) or not {"provider", "flow"} <= set(graph):
            errors.append(f"{template.name}: provenance frontmatter is missing required fields")
        if not isinstance(generator, dict) or not {"name", "version"} <= set(generator):
            errors.append(f"{template.name}: provenance frontmatter is missing generator")
        if provenance.get("schema") != SCHEMA_VERSION or "graph_snapshot" in provenance:
            errors.append(f"{template.name}: provenance frontmatter must use schema 2.0")
    scripts = SKILL_ROOT / "scripts"
    py_names = {path.stem for path in scripts.glob("*.py")}
    js_names = {path.stem for path in scripts.glob("*.js")}
    for name in sorted(py_names - js_names):
        errors.append(f"missing Node peer for {name}.py")
    for name in sorted(js_names - py_names):
        errors.append(f"missing Python peer for {name}.js")
    for name, tokens in PUBLIC_CONTRACTS.items():
        for suffix in ("py", "js"):
            text = (scripts / f"{name}.{suffix}").read_text(encoding="utf-8")
            missing = [token for token in tokens if token not in text]
            if missing:
                errors.append(f"{name}.{suffix}: missing CLI contract tokens: {', '.join(missing)}")
    meta = read_json(REPO_ROOT / "meta.json")
    plugin = read_json(REPO_ROOT / ".claude-plugin" / "plugin.json")
    market = read_json(REPO_ROOT / ".claude-plugin" / "marketplace.json")["plugins"][0]
    versions = {meta.get("version"), plugin.get("version"), market.get("version"), catalog.get("version")}
    if versions != {"2.1.0"}:
        errors.append(f"release versions disagree: {sorted(str(item) for item in versions)}")
    skill_text = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
    skill_match = re.search(r"^description: (.+)$", skill_text, re.MULTILINE)
    entry_description = meta.get("skills", {}).get("entries", [{}])[0].get("description")
    descriptions = {
        meta.get("description"), plugin.get("description"), market.get("description"),
        entry_description, skill_match.group(1) if skill_match else None,
    }
    if len(descriptions) != 1:
        errors.append("package descriptions disagree")
    forbidden_files = {
        "document" + "-templates.json",
        "generation" + "-status.json",
        "status" + "-schema.json",
        "template" + "-schema.json",
    }
    present = forbidden_files & {path.name for path in metadata.iterdir()}
    if present:
        errors.append(f"obsolete metadata files remain: {', '.join(sorted(present))}")
    legacy_constants = ["SP" + "INE", "SPINE_" + "PLAN", "OVER" + "LAYS"]
    duplicate_constants = re.compile(r"\b(" + "|".join(legacy_constants) + r")\s*=")
    for script in sorted(scripts.glob("*.[pj][ys]")):
        if duplicate_constants.search(script.read_text(encoding="utf-8", errors="ignore")):
            errors.append(f"{script.name}: duplicated registry constant")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    errors = validate()
    if errors:
        for error in errors:
            print(f"ERROR  {error}")
        print(f"\n{len(errors)} metadata errors.")
        return 1
    print("OK  catalog, schemas, templates, runtime peers, and package metadata agree.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
