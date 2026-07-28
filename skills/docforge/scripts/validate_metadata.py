#!/usr/bin/env python3
"""Validate the Docforge catalog, schemas, templates, peers, and release metadata."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = SKILL_ROOT.parent.parent
REQUIRED_DOC_FIELDS = {
    "id", "type", "path", "group", "selection", "scaffold_template",
    "requires", "target_depth", "write_order", "provenance_mode", "audit_profile",
}
MARKDOWN_EXCEPTIONS = {"agents-kernel.md", "claude-md.md", "claude-local-md.md"}
PUBLIC_CONTRACTS = {
    "manage_manifest": ["init", "add", "set", "status", "audit", "--repo", "--tier", "--overlay", "--type", "--id", "--path", "--status", "--mode", "--verdict", "--report"],
    "scaffold_docs": ["--repo", "--manifest", "--dry-run", "--document", "--audit"],
    "precheck_graph": ["--repo", "--need", "code", "flow"],
    "check_staleness": ["--manifest", "--section", "--json", "--sync-provenance"],
}


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def validate() -> list[str]:
    errors: list[str] = []
    metadata = SKILL_ROOT / ".metadata"
    catalog = read_json(metadata / "catalog.json")
    catalog_schema = read_json(metadata / "catalog-schema.json")
    manifest_schema = read_json(metadata / "manifest-schema.json")
    if catalog.get("version") != "1.0.0":
        errors.append("catalog version must be 1.0.0")
    if catalog_schema.get("properties", {}).get("version", {}).get("const") != "1.0.0":
        errors.append("catalog schema version disagrees with catalog")
    if manifest_schema.get("properties", {}).get("version", {}).get("const") != "2.0":
        errors.append("manifest schema must require version 2.0")
    tiers = {item["id"] for item in catalog.get("tiers", [])}
    overlays = {item["id"] for item in catalog.get("overlays", [])}
    groups = set(catalog.get("groups", []))
    capabilities = set(catalog.get("capabilities", []))
    static_ids: set[str] = set()
    static_paths: set[str] = set()
    dynamic_types: set[str] = set()
    for index, doc in enumerate(catalog.get("documents", [])):
        label = doc.get("id", f"document[{index}]")
        missing = sorted(REQUIRED_DOC_FIELDS - set(doc))
        if missing:
            errors.append(f"{label}: missing fields: {', '.join(missing)}")
            continue
        selection = doc.get("selection", {})
        if doc["group"] not in groups:
            errors.append(f"{label}: unknown group {doc['group']}")
        if selection.get("min_tier") not in tiers:
            errors.append(f"{label}: unknown tier {selection.get('min_tier')}")
        for overlay in selection.get("overlays", []):
            if overlay not in overlays:
                errors.append(f"{label}: unknown overlay {overlay}")
        for overlay in selection.get("include_if_overlay", []):
            if overlay not in overlays:
                errors.append(f"{label}: unknown include_if_overlay {overlay}")
        for requirement in doc.get("requires", []):
            if requirement not in capabilities:
                errors.append(f"{label}: unknown requirement {requirement}")
        if not isinstance(doc.get("write_order"), int):
            errors.append(f"{label}: write_order must be an integer")
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
        if not text.startswith("---\n{"):
            errors.append(f"{template.name}: provenance frontmatter must start at byte one")
            continue
        end = text.find("\n---\n", 4)
        try:
            frontmatter = json.loads(text[4:end]) if end >= 0 else None
        except json.JSONDecodeError:
            frontmatter = None
        if not isinstance(frontmatter, dict) or "docforge_provenance" not in frontmatter:
            errors.append(f"{template.name}: provenance frontmatter is not valid JSON")
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
    if versions != {"1.0.0"}:
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
