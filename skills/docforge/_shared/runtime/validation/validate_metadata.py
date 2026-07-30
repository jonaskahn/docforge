#!/usr/bin/env python3
"""Validate the Docforge catalog, schemas, templates, peers, and release metadata."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from runtime.common._util import read_json
from runtime.common.provenance_frontmatter import PROVENANCE_FIELDS, SCHEMA_VERSION, parse_frontmatter
from . import generate_indexes
from runtime.catalog import query_catalog

SKILL_ROOT = Path(__file__).resolve().parent.parent.parent
REPO_ROOT = SKILL_ROOT.parent.parent
CATALOG_VERSION = "2.6.1"
MARKDOWN_EXCEPTIONS = {"agents-kernel.md", "claude-md.md", "claude-local-md.md"}
PUBLIC_CONTRACTS = {
    "manage_manifest": ["init", "add", "set", "status", "audit", "--repo", "--tier", "--shape", "--platform", "--framework", "--concern", "--audience", "--type", "--id", "--path", "--status", "--mode", "--verdict", "--report"],
    "detect_profiles": ["--repo", "--json", "--emit-gate-pack", "confirmed", "candidate"],
    "scaffold_docs": ["--repo", "--manifest", "--dry-run", "--document", "--audit"],
    "precheck_graph": ["--repo", "--need", "code", "flow"],
    "check_staleness": ["--manifest", "--document", "--section", "--json", "--sync-provenance"],
    "flow_index": ["harvest", "revise", "render", "organize", "emit", "apply", "--repo", "--gitnexus-export", "--main-limit", "--output", "--organization"],
    "migrate_metadata": ["--repo", "--manifest", "--dry-run", "--report"],
    "query_catalog": ["--tier", "--id", "--ids", "--profile", "--applicable", "--validate", "--category", "--route"],
    "generate_indexes": ["--write", "--check"],
}


def validate() -> list[str]:
    errors: list[str] = []
    metadata = SKILL_ROOT / ".metadata"
    # Catalog shape checks live in query_catalog --validate (single source of truth).
    errors.extend(query_catalog.validate())
    try:
        stale = generate_indexes.stale_targets()
        for path in stale:
            errors.append(f"generated router is stale: {path.relative_to(SKILL_ROOT)} (run generate_indexes --write)")
    except ValueError as exc:
        errors.append(f"generate_indexes --check failed: {exc}")
    try:
        catalog = query_catalog.as_legacy_catalog()
    except ValueError as exc:
        errors.append(str(exc))
        catalog = {"version": None, "documents": [], "profiles": {}, "tiers": []}
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
    if catalog.get("version") != CATALOG_VERSION:
        errors.append(f"catalog version must be {CATALOG_VERSION}")
    if catalog_schema.get("properties", {}).get("version", {}).get("const") != CATALOG_VERSION:
        errors.append("catalog schema version disagrees with catalog")
    if not (metadata / "catalog" / "index.json").is_file():
        errors.append("split catalog index.json is missing")
    if (metadata / "catalog.json").is_file():
        errors.append("obsolete monolith catalog.json remains; use .metadata/catalog/")
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
    for dimension in dimensions:
        definitions = profiles.get(dimension, [])
        if not definitions:
            errors.append(f"{dimension}: profile registry must not be empty")
        orders = [item.get("order") for item in definitions]
        if len(set(orders)) != len(orders) or not all(isinstance(item, int) for item in orders):
            errors.append(f"{dimension}: profile order values must be unique integers")
        for item in definitions:
            identifier = item.get("id")
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
                strength = signal.get("strength")
                if strength is not None and strength not in {"strong", "weak"}:
                    errors.append(f"{dimension}/{identifier}: signal strength must be strong|weak")
                weight = signal.get("weight")
                if weight is not None and (
                    not isinstance(weight, (int, float)) or weight <= 0 or weight > 1
                ):
                    errors.append(f"{dimension}/{identifier}: signal weight must be in (0, 1]")
    cross_aliases: dict[str, list[str]] = {}
    for dimension in dimensions:
        for item in profiles.get(dimension, []):
            for name in [item.get("id"), *item.get("aliases", [])]:
                if isinstance(name, str):
                    cross_aliases.setdefault(name, []).append(f"{dimension}:{item.get('id')}")
    for name, owners in sorted(cross_aliases.items()):
        if len(owners) > 1:
            errors.append(f"cross-dimension profile name collision {name}: {', '.join(owners)}")
    for hint in catalog.get("cue_hints", []):
        if not isinstance(hint, dict) or not hint.get("cue") or not hint.get("note"):
            errors.append("cue_hints entries require cue and note")
    gate_schema_path = metadata / "discovery-gate-schema.json"
    if not gate_schema_path.is_file():
        errors.append("discovery-gate-schema.json is missing")
    else:
        gate_schema = read_json(gate_schema_path)
        if "judgment" not in gate_schema.get("definitions", {}):
            errors.append("discovery-gate-schema.json must define judgment")
        if "pack" not in gate_schema.get("definitions", {}):
            errors.append("discovery-gate-schema.json must define pack")
    for index, doc in enumerate(catalog.get("documents", [])):
        label = doc.get("id", f"document[{index}]")
        selection = doc.get("selection", {})
        obsolete = {"overlays", "include_if_overlay"} & set(selection)
        if obsolete:
            errors.append(f"{label}: obsolete selection fields: {', '.join(sorted(obsolete))}")
    # Drive the template scan from the catalog itself (template_file paths
    # now vary by group/kind under content/) plus the two shared templates
    # with no catalog reference (audit-report, audience-deepdive).
    template_paths = {
        SKILL_ROOT / detail["template_file"]
        for detail in query_catalog.load_all_types()
        if detail["template_file"].endswith(".md")
    }
    template_paths |= {
        SKILL_ROOT / "content" / "shared" / name
        for name in ("audit-report.template.md", "audience-deepdive.template.md")
    }
    for template in sorted(template_paths):
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
    cli_py = SKILL_ROOT / "runtime" / "cli" / "python"
    cli_js = SKILL_ROOT / "runtime" / "cli" / "js"
    # One-shot migration helpers; not part of the dual-runtime public surface.
    peerless = {"split_catalog", "split_document_catalog"}
    py_names = {path.stem for path in cli_py.glob("*.py")} - peerless
    js_names = {path.stem for path in cli_js.glob("*.js")} - peerless
    for name in sorted(py_names - js_names):
        errors.append(f"missing Node peer for {name}.py")
    for name in sorted(js_names - py_names):
        errors.append(f"missing Python peer for {name}.js")
    runtime_root = SKILL_ROOT / "runtime"

    def impl_matches(name: str, suffix: str) -> list[Path]:
        return [
            path
            for path in runtime_root.rglob(f"{name}.{suffix}")
            if "cli" not in path.relative_to(runtime_root).parts
        ]

    for name, tokens in PUBLIC_CONTRACTS.items():
        for suffix in ("py", "js"):
            # CLI flags live in the runtime implementation; the cli/
            # launcher is a thin re-export with no flag text.
            matches = impl_matches(name, suffix)
            fallback = (cli_py if suffix == "py" else cli_js) / f"{name}.{suffix}"
            source = matches[0] if matches else fallback
            text = source.read_text(encoding="utf-8")
            missing = [token for token in tokens if token not in text]
            if missing:
                errors.append(f"{name}.{suffix}: missing CLI contract tokens: {', '.join(missing)}")
    plugin = read_json(REPO_ROOT / ".claude-plugin" / "plugin.json")
    market = read_json(REPO_ROOT / ".claude-plugin" / "marketplace.json")["plugins"][0]
    versions = {plugin.get("version"), market.get("version"), catalog.get("version")}
    if versions != {CATALOG_VERSION}:
        errors.append(f"release versions disagree: {sorted(str(item) for item in versions)}")
    skill_text = (REPO_ROOT / "skills" / "docforge" / "SKILL.md").read_text(encoding="utf-8")
    skill_match = re.search(r"^description: (.+)$", skill_text, re.MULTILINE)
    revise_text = (REPO_ROOT / "skills" / "docforge-revise" / "SKILL.md").read_text(encoding="utf-8")
    revise_match = re.search(r"^description: (.+)$", revise_text, re.MULTILINE)
    if not skill_match:
        errors.append("skills/docforge/SKILL.md missing description frontmatter")
    if not revise_match:
        errors.append("skills/docforge-revise/SKILL.md missing description frontmatter")
    descriptions = {
        plugin.get("description"),
        market.get("description"),
        skill_match.group(1) if skill_match else None,
    }
    if len(descriptions) != 1:
        errors.append("package descriptions disagree (plugin, marketplace, docforge SKILL.md)")
    if (REPO_ROOT / "meta.json").exists():
        errors.append("obsolete meta.json remains; Agent Skills install uses SKILL.md only")
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
    scannable = (
        list(cli_py.glob("*.py"))
        + list(cli_js.glob("*.js"))
        + [path for path in runtime_root.rglob("*.[pj][ys]") if "cli" not in path.relative_to(runtime_root).parts]
    )
    for script in sorted(scannable):
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
