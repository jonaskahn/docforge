#!/usr/bin/env python3
"""Create and maintain a Docforge manifest from the canonical catalog."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

from runtime.common.python._util import (
    dump_json,
    ensure_docforge_gitignore,
    ensure_gitignored_dir,
    fail,
    finish_docforge,
    load_manifest,
)
from runtime.common.python.agent_context import AGENT_CONTEXT_GROUP
from runtime.common.python.plan import plan_lines
from runtime.common.python import scale
from runtime.catalog.python.detect_profiles import detect as detect_profiles
from runtime.catalog.python.detect_profiles import inventory as inventory_files
from runtime.common.python import provenance_store as store
from runtime.common.python.provenance_frontmatter import GENERATOR_VERSION, scaffold_provenance
from runtime.catalog.python import query_catalog
from runtime.graph.python.graph_source_registry import SOURCES as GRAPH_SOURCES, flow_capability_of, resolve_all_ready, resolve_first_ready

SKILL_ROOT = Path(__file__).resolve().parent.parent.parent.parent
MANIFEST_REL = Path(".docforge/manifest.json")
FLOW_INDEX_REL = Path(".docforge/flow-index.json")
STATUSES = ["planned", "in_progress", "generated", "needs_review", "complete", "skipped", "retired"]
WRITTEN = {"generated", "needs_review", "complete"}
TRANSITIONS = {
    "planned": {"in_progress", "skipped"},
    "in_progress": {"generated", "needs_review", "skipped"},
    "generated": {"needs_review", "complete", "skipped"},
    "needs_review": {"in_progress", "skipped"},
    "complete": {"in_progress"},
    "skipped": {"planned"},
    "retired": {"planned"},
}
TOOL_VERSION = GENERATOR_VERSION
MANIFEST_VERSION = "3.10"
USER_CONFIRMED_TRIGGERS = {
    "new-trust-boundary", "per-interaction-review", "regulated-workload",
    "high-criticality", "new-external-integration", "new-data-classification",
}


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


MANIFEST_HINT = (
    "run migrate_metadata.py to re-register legacy manifests"
)


def load_catalog() -> dict:
    return query_catalog.as_legacy_catalog()


def manifest_path(repo: Path) -> Path:
    return repo / MANIFEST_REL


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
        "retired": sum(d["status"] == "retired" for d in docs),
        "last_updated": now_iso(),
    }
    path = manifest_path(repo)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dump_json(manifest), encoding="utf-8")
    ensure_docforge_gitignore(path.parent)
    ensure_gitignored_dir(path.parent / "tmp")
    ensure_gitignored_dir(path.parent / "audits")


def condition_evidence(repo: Path, condition: str | None) -> list[str]:
    if condition is None:
        return []
    if condition == "conventions_source":
        candidates = [
            "CONVENTIONS.md", "docs/CONVENTIONS.md", "docs/conventions.md",
            ".editorconfig", "STYLEGUIDE.md",
        ]
        return [candidate for candidate in candidates if (repo / candidate).exists()]
    if condition == "ticket_evidence":
        candidates = [
            ".docforge/tickets.json", "tickets.json", "backlog.json",
            "BACKLOG.md", "docs/backlog.md", ".github/ISSUE_TEMPLATE",
        ]
        return [candidate for candidate in candidates if (repo / candidate).exists()]
    if condition == "multi_flow_repo":
        # Threshold: more than one main-priority row in the flow index.
        path = repo / FLOW_INDEX_REL
        if not path.is_file():
            return []
        try:
            index = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return []
        main_count = sum(
            1 for row in index.get("flows", []) if flow_is_main_priority(row)
        )
        return [str(FLOW_INDEX_REL)] if main_count > 1 else []
    # discovered_* and other agent-asserted conditions: no filesystem evidence.
    return []


def validate_relative_path(value: str) -> None:
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or value in ("", "."):
        raise ValueError(f"path must be a safe repository-relative path: {value}")


def validate_selection_evidence(repo: Path, values: list[str]) -> list[str]:
    """Validate bounded CLI evidence without placing free-form text in manifests."""
    validated: list[str] = []
    for value in values:
        if "\n" in value:
            raise ValueError("selection evidence must not contain newlines")
        if value.startswith("path:"):
            rel = value.removeprefix("path:")
            validate_relative_path(rel)
            if not (repo / rel).is_file():
                raise ValueError(f"selection evidence path does not exist: {rel}")
        elif value.startswith("graph:"):
            if re.fullmatch(r"graph:[a-z0-9][a-z0-9-]*:[A-Za-z0-9._:/-]+", value) is None:
                raise ValueError(f"invalid graph selection evidence: {value}")
        elif value.startswith("user-confirmed:"):
            trigger = value.removeprefix("user-confirmed:")
            if trigger not in USER_CONFIRMED_TRIGGERS:
                raise ValueError(f"unregistered user-confirmed trigger: {trigger}")
        else:
            raise ValueError(f"selection evidence must use path:, graph:, or user-confirmed:: {value}")
        if value not in validated:
            validated.append(value)
    return validated


def make_document(
    definition: dict,
    origins: list[dict],
    evidence: list[str] | None = None,
    *,
    catalog_id: str | None = None,
    audiences: list[str] | None = None,
) -> dict:
    # `definition` comes from the legacy-view catalog (bare filenames, kept
    # stable for --legacy CLI output); the manifest's scaffold_template must
    # be a skill-root-relative path so scaffold_docs.py can locate the file
    # after Phase 5 moved content artifacts out of one flat directory. For
    # dynamic types, `definition["id"]` is already the per-instance manifest
    # id by the time this runs, so callers pass the original catalog id
    # explicitly via `catalog_id`.
    detail = query_catalog.load_type(catalog_id or definition["id"])
    primary_audience, presentation, _ = query_catalog.resolve_presentation(detail, audiences)
    document = {
        "id": definition["id"],
        "title": detail.get("title") or definition["id"].replace("_", " ").replace("-", " ").title(),
        "description": detail.get("summary") or "",
        "type": definition["type"],
        "path": definition["path"],
        "group": definition["group"],
        "selection": {
            "origins": origins,
            "evidence": evidence or [],
        },
        "status": "planned",
        "requires": list(definition["requires"]),
        "scaffold_template": detail["template_file"],
        "instruction_file": detail.get("instruction_file"),
        "target_depth": definition["target_depth"],
        "write_order": definition["write_order"],
        "provenance_mode": definition["provenance_mode"],
        "audit_profile": definition["audit_profile"],
        "dominant_form": detail.get("dominant_form"),
        "presentation": {"primary_audience": primary_audience, **presentation},
        "provenance": scaffold_provenance(
            definition["id"],
            definition["path"],
            target_depth=definition["target_depth"],
        ),
        "audit": None,
    }
    if detail.get("contract_revision") is not None:
        document["contract_revision"] = detail["contract_revision"]
    if detail.get("nav_order") is not None:
        document["nav_order"] = detail["nav_order"]
    return document


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


def _compact_member_key(pair: tuple[int, dict]) -> tuple[int, str]:
    """Order members by `compact_order`, then id. The id tiebreak is required:
    `compact_order` defaults to 0, so two members without an explicit order
    would otherwise fall through to comparing the document dicts themselves."""
    order, doc = pair
    return (order, doc["id"])


def fold_compact_groups(
    catalog: dict,
    selected: list[dict],
    audiences: list[str],
) -> tuple[list[dict], set[str]]:
    """Compact-layout fold: replace every selected document whose catalog
    record declares a `compact_group` with the group's single merged entry at
    its `compact_target`, members recorded on the entry so provenance and
    revise can trace them back. Strictly gated on `layout == "compact"` by the
    caller — a standard run never folds. Member entries are synthesized from
    catalog data only; folded member ids are returned so ancestor-index
    computation skips resurrecting them.

    A group whose selected membership exceeds `COMPACT_SECTION_CAP` **spills**:
    the merged file keeps its core members plus profile-driven ones in
    `compact_order` until the cap is reached, and the overflow stays at its own
    standard path, linked from the merged file. That is the pre-fold behavior,
    so a pathological many-shape repository degrades to the standard tree
    instead of producing one unreadable file."""
    by_id = {doc["id"]: doc for doc in catalog["documents"]}
    groups: dict[str, list[tuple[int, dict]]] = {}
    kept: list[dict] = []
    for doc in selected:
        detail = query_catalog.load_type(doc["id"])
        group_id = detail.get("compact_group")
        if group_id:
            order = detail.get("compact_order", 0)
            groups.setdefault(group_id, []).append((order, doc))
        else:
            kept.append(doc)
    folded_ids: set[str] = set()
    for group_id, members in sorted(groups.items()):
        definition = by_id.get(group_id)
        if definition is None or definition.get("selection", {}).get("mode") != "compact":
            kept.extend(doc for _, doc in sorted(members, key=_compact_member_key))
            continue
        members.sort(key=_compact_member_key)
        spilled = members[query_catalog.COMPACT_SECTION_CAP:]
        members = members[:query_catalog.COMPACT_SECTION_CAP]
        kept.extend(doc for _, doc in spilled)
        merged = make_document(
            definition,
            [
                {"kind": "tier", "id": definition["selection"]["min_tier"]},
                {"kind": "compact", "id": group_id},
            ],
            audiences=audiences,
        )
        merged["compact_members"] = [doc["id"] for _, doc in members]
        folded_ids.update(doc["id"] for _, doc in members)
        kept.append(merged)
    return kept, folded_ids


def compact_group_ids(catalog: dict) -> set[str]:
    """Every catalog id that declares a `compact_group`, selected this run or
    not. `add_ancestor_indexes` needs the full set, not just what folded: a
    Diligence-only index such as `security_index` is never selected at Spine,
    so it never folds, and the ancestor pass would otherwise resurrect
    `docs/security/README.md` inside a compact tree."""
    return {
        item["id"] for item in catalog["documents"]
        if query_catalog.load_type(item["id"]).get("compact_group")
    }


def add_ancestor_indexes(
    catalog: dict,
    selected: list[dict],
    audiences: list[str],
    *,
    skip_ids: set[str] | None = None,
) -> None:
    definitions = {
        item["path"]: item for item in catalog["documents"]
        if item["selection"]["mode"] == "static" and item["type"] in {
            "folder-index", "docs-index", "portfolio-index",
            "decision-index", "portfolio-decisions-index", "flow-index",
        }
    }
    skipped = skip_ids or set()
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
                if (
                    definition
                    and definition["id"] not in skipped
                    and candidate not in selected_paths
                ):
                    selected.append(make_document(
                        definition,
                        [{"kind": "ancestor", "id": child["id"]}],
                        audiences=audiences,
                    ))
                    selected_paths.add(candidate)
                    changed = True
                parent = parent.parent


def empty_selection_message(groups: list[str], profiles: dict[str, list[str]]) -> str:
    """Explain an empty selection by naming the audience that would unlock it.

    Every agent-context type is gated on `coding-agents`, so `--group
    agent-context` alone selects nothing; saying so beats writing an empty
    manifest or a bare count of zero."""
    if not groups:
        return "no documents selected for this tier and profile set"
    missing: list[str] = []
    for group in groups:
        unlocking = query_catalog.group_audiences(group)
        if unlocking and not any(a in profiles["audiences"] for a in unlocking):
            missing.append(f"{group} requires audience {' or '.join(unlocking)}")
    detail = f"; {'; '.join(missing)}" if missing else ""
    return (
        f"no documents selected: group scope {', '.join(groups)}{detail}"
        f" — add the audience or widen --group"
    )


def selected_static_documents(
    catalog: dict,
    repo: Path,
    tier: str,
    profiles: dict[str, list[str]],
    layout: str = "standard",
    groups: list[str] | None = None,
) -> list[dict]:
    """`groups` restricts the run to those catalog groups; empty means all.

    The filter is strictly subtractive and runs before every other test, so it
    can never add a document and skips `condition_evidence` filesystem work for
    out-of-scope types."""
    ranks = {item["id"]: item["order"] for item in catalog["tiers"]}
    scoped = set(groups or [])
    selected: list[dict] = []
    for definition in catalog["documents"]:
        rule = definition["selection"]
        if rule["mode"] != "static":
            continue
        if scoped and definition.get("group") not in scoped:
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
        selected.append(make_document(definition, origins, evidence, audiences=profiles["audiences"]))
    skip_ids: set[str] = set()
    if layout == "compact":
        selected, _ = fold_compact_groups(catalog, selected, profiles["audiences"])
        skip_ids = compact_group_ids(catalog)
    if scoped:
        # An out-of-scope index must not be pulled back in as an ancestor: an
        # agents-only run writes no docs/README.md, and a docs/README.md that
        # indexed only docs/agents/ would be the human->agent reference the
        # isolation boundary forbids.
        skip_ids = skip_ids | {
            definition["id"] for definition in catalog["documents"]
            if definition.get("group") not in scoped
        }
    add_ancestor_indexes(catalog, selected, profiles["audiences"], skip_ids=skip_ids)
    return sorted(selected, key=lambda item: (item["write_order"], item["path"], item["id"]))


def resolve_graph_lock(repo: Path, provider: str | None) -> dict | None:
    """Resolve the graph provider to lock: `provider` if given (validated
    against the registry and current readiness), else the highest-priority
    ready source (registry order — the same order --auto-accept already uses).
    Returns None when nothing is ready. Raises ValueError for an invalid or
    not-ready explicit `provider`."""
    if provider:
        known = {source["name"] for source in GRAPH_SOURCES}
        if provider not in known:
            raise ValueError(
                f"unknown graph provider: {provider}; expected one of: {', '.join(sorted(known))}"
            )
        ready_names = {source["name"] for source, _ in resolve_all_ready(repo, "code_graph")}
        if provider not in ready_names:
            raise ValueError(f"graph provider {provider} is not ready in this repo")
        chosen = provider
    else:
        source, _ = resolve_first_ready(repo, "code_graph")
        if source is None:
            return None
        chosen = source["name"]
    # flow_capability_of, not precheck's report_flow_graph: the stored value must
    # describe the *chosen* provider. The repo-wide question answered "native" for
    # a CodeGraph lock whenever an unrelated .ua/domain-graph.json existed, which
    # is the "Native flow source: CodeGraph" claim graph-sources.md forbids.
    return {"provider": chosen, "flow": flow_capability_of(repo, chosen), "locked_at": now_iso()}


def resolve_scale(
    repo: Path,
    scale_class: str | None,
    layout: str | None,
    files: list | None = None,
    detections: list[dict] | None = None,
    tier: str = "diligence",
) -> dict:
    """Build the `project.scale` record. Omitted flags adopt detection; any
    explicit flag records `decided_by: "user"` with `detected_class` preserved
    so a later run never silently re-classifies an override. `files` and
    `detections` let a caller that already walked the repo avoid a second walk.

    `tier` gates the layout through `scale.layout_for`: an explicit compact
    pick at Portfolio raises `scale.LayoutTierError`, and a detected compact
    layout there is forced to standard as `decided_by: "tier-constraint"`."""
    detected = scale.compute_scale(repo, files=files, detections=detections)
    if scale_class is None and layout is None:
        chosen_layout, decided_by = scale.layout_for(
            tier, detected["suggested_layout"], explicit=False
        )
        record = {
            "class": detected["class"],
            "layout": chosen_layout,
            "decided_by": decided_by,
            "decided_at": now_iso(),
            "signals": detected["signals"],
        }
        if decided_by == "tier-constraint":
            record["detected_class"] = detected["class"]
        return record
    chosen_class = scale_class or detected["class"]
    chosen_layout, constraint = scale.layout_for(
        tier,
        layout or scale.LAYOUT_BY_CLASS[chosen_class],
        explicit=layout is not None,
    )
    # Either flag being present makes this a user decision; the tier can still
    # override the layout it implied, and that override is what gets recorded.
    return {
        "class": chosen_class,
        "layout": chosen_layout,
        "detected_class": detected["class"],
        "decided_by": "tier-constraint" if constraint == "tier-constraint" else "user",
        "decided_at": now_iso(),
        "signals": detected["signals"],
    }


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
    # One walk feeds both the discovery record and the scale record.
    walked = inventory_files(args.repo)
    discovery = detect_profiles(args.repo, files=walked)
    try:
        project_scale = resolve_scale(
            args.repo, args.scale_class, args.layout,
            files=walked, detections=discovery, tier=args.tier,
        )
    except scale.LayoutTierError as exc:
        return fail(str(exc), 2)
    try:
        scoped_groups = query_catalog.normalize_groups(list(getattr(args, "group", []) or []))
    except ValueError as exc:
        return fail(str(exc), 2)
    docs = selected_static_documents(
        catalog, args.repo, args.tier, profiles, layout=project_scale["layout"],
        groups=scoped_groups,
    )
    if not docs:
        return fail(empty_selection_message(scoped_groups, profiles), 2)
    manifest = {
        "version": MANIFEST_VERSION,
        "generated_at": now_iso(),
        "project": {
            "name": args.name or args.repo.resolve().name,
            "root": str(args.repo.resolve()),
            "tier": args.tier,
            "scale": project_scale,
            "profiles": profiles,
            "provenance_storage": store.STORAGE_JSON,
            "unmanaged_docs": [],
        },
        "discovery": discovery,
        "discovery_gate": None,
        "documents": docs,
        "metadata": {},
    }
    # An unscoped run genuinely has no group scope.
    if scoped_groups:
        manifest["project"]["groups"] = scoped_groups
    try:
        graph_lock = resolve_graph_lock(args.repo, args.graph_provider)
    except ValueError as exc:
        return fail(str(exc), 2)
    if graph_lock is not None:
        manifest["graph"] = graph_lock
    save_manifest(args.repo, manifest)
    print(f"Wrote {path} — tier {args.tier}, {len(docs)} static documents planned.")
    if graph_lock is not None:
        print(f"Locked graph provider: {graph_lock['provider']} (flow: {graph_lock['flow']})")
    else:
        print("No graph provider ready yet — run `set-graph` once a code graph is built.")
    print()
    for line in plan_lines(args.repo, manifest, args.repo / ".docforge" / "flow-index.json"):
        print(line)
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


def compact_host_for(manifest: dict, full_definition: dict) -> dict | None:
    """The merged manifest entry that hosts this dynamic type as a `##`
    section, or None when the instance gets its own file. None covers every
    standard-layout project, a type with no `compact_group`, and a group that
    spilled past `COMPACT_SECTION_CAP` — in all three the pre-fold path is
    correct."""
    if manifest["project"].get("scale", {}).get("layout") != "compact":
        return None
    group_id = full_definition.get("compact_group")
    if not group_id:
        return None
    for doc in manifest["documents"]:
        if doc.get("id") == group_id and isinstance(doc.get("compact_members"), list):
            return doc
    return None


def section_slug(path: str) -> str:
    return PurePosixPath(path).stem


def add_compact_section(
    args: argparse.Namespace,
    manifest: dict,
    definition: dict,
    full_definition: dict,
    merged: dict,
    flow_index: dict | None,
    flow_row: dict | None,
) -> int:
    """Record a discovered instance as a `##` section of its group's merged
    file instead of a document of its own. The section descriptor keeps the
    dynamic type id — so the section is still written from that type's contract
    and template — plus the slug and title that name it, which is what
    provenance and a later compact -> standard `split` need to rebuild the
    component file."""
    slug = section_slug(args.path)
    existing = merged["compact_members"]
    sections = [item for item in existing if isinstance(item, dict)]
    if any(item.get("id") == definition["id"] and item.get("slug") == slug for item in sections):
        return fail(f"section already exists in {merged['path']}: {slug}", 2)
    same_type = [item for item in sections if item.get("id") == definition["id"]]
    if len(same_type) >= query_catalog.COMPACT_DYNAMIC_CAP:
        return fail(
            f"{merged['path']} already carries {query_catalog.COMPACT_DYNAMIC_CAP} "
            f"{definition['type']} sections, the compact section budget; "
            f"'{slug}' stays a row in that file's candidate matrix",
            2,
        )
    title = args.title or slug.replace("-", " ").replace("_", " ").capitalize()
    existing.append({"id": definition["id"], "slug": slug, "title": title})
    merged["requires"] = sorted(set(merged.get("requires", [])) | set(definition["requires"]))
    save_manifest(args.repo, manifest)
    if flow_index is not None and flow_row is not None:
        flow_row["status"] = "documented"
        (args.repo / FLOW_INDEX_REL).write_text(dump_json(flow_index), encoding="utf-8")
    print(f"Added {slug} as a {definition['type']} section of {merged['path']} (compact layout).")
    return 0


def cmd_add(args: argparse.Namespace) -> int:
    flow_index = None
    flow_row = None
    try:
        manifest = load_manifest(
            manifest_path(args.repo),
            unsupported_hint=MANIFEST_HINT,
        )
        catalog = load_catalog()
        definition = dynamic_definition(catalog, args.type)
        project_groups = set(manifest["project"].get("groups", []))
        if project_groups and definition.get("group") not in project_groups:
            raise ValueError(
                f"dynamic type {args.type} belongs to out-of-scope group "
                f"{definition.get('group')}"
            )
        full_definition = query_catalog.load_type(definition["id"])
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
    try:
        evidence.extend(validate_selection_evidence(args.repo, args.evidence))
    except ValueError as exc:
        return fail(str(exc), 2)
    if flow_row is not None:
        evidence = [str(FLOW_INDEX_REL), *[
            str(item.get("artifact"))
            for item in flow_row.get("evidence", [])
            if item.get("artifact")
        ]]
    if rule.get("condition") == "ticket_evidence" and not evidence:
        return fail(f"dynamic type {args.type} requires ticket evidence in the repository", 2)
    if full_definition.get("selection_evidence_required") and not evidence:
        return fail(f"dynamic type {args.type} requires selection evidence", 2)
    if not path_matches(definition["path"], args.path):
        return fail(f"path '{args.path}' does not match catalog pattern '{definition['path']}'", 2)
    if re.fullmatch(r"[a-z0-9][a-z0-9_-]*", args.id) is None:
        return fail(f"document id must use lowercase letters, digits, hyphens, or underscores: {args.id}", 2)
    if any(doc["id"] == args.id for doc in manifest["documents"]):
        return fail(f"document id already exists: {args.id}", 2)
    if any(doc["path"] == args.path for doc in manifest["documents"]):
        return fail(f"document path already exists: {args.path}", 2)
    merged = compact_host_for(manifest, full_definition)
    if merged is not None:
        return add_compact_section(args, manifest, definition, full_definition, merged, flow_index, flow_row)
    actual = dict(definition)
    actual["id"] = args.id
    actual["path"] = args.path
    if args.title:
        actual["title"] = args.title
    origins = [{"kind": "dynamic", "id": definition["type"]}, *profile_origins]
    if rule.get("condition"):
        origins.append({"kind": "condition", "id": rule["condition"]})
    doc = make_document(
        actual,
        origins,
        evidence,
        catalog_id=definition["id"],
        audiences=manifest["project"]["profiles"]["audiences"],
    )
    manifest["documents"].append(doc)
    manifest["documents"].sort(key=lambda item: (item["write_order"], item["path"], item["id"]))
    save_manifest(args.repo, manifest)
    if flow_index is not None and flow_row is not None:
        flow_row["status"] = "documented"
        (args.repo / FLOW_INDEX_REL).write_text(dump_json(flow_index), encoding="utf-8")
    print(f"Added {args.id} ({args.path}) as dynamic type {args.type}.")
    return 0


def catalog_id_for_document(catalog: dict, doc: dict) -> str | None:
    if doc["id"] == doc.get("type"):
        return doc["id"]
    for candidate in catalog["documents"]:
        if candidate["id"] == doc.get("id"):
            return candidate["id"]
        if (
            candidate.get("type") == doc.get("type")
            and candidate.get("selection", {}).get("mode") == "dynamic"
        ):
            return candidate["id"]
    return None


def effective_presentation(catalog_id: str, audiences: list[str], override: dict | None = None) -> dict:
    detail = query_catalog.load_type(catalog_id)
    effective_override = dict(override or {})
    if detail.get("presentation", {}).get("related_docs") == "none":
        effective_override.pop("related_docs", None)
    if effective_override:
        detail = {
            **detail,
            "presentation": {**detail.get("presentation", {}), **effective_override},
        }
    primary, presentation, _ = query_catalog.resolve_presentation(detail, audiences)
    return {"primary_audience": primary, **presentation}


def demote_written(doc: dict) -> None:
    """Send a written document back for re-grounding, clearing its audit.

    Shared by every mechanical trigger that invalidates existing prose."""
    if doc["status"] in {"generated", "needs_review", "complete"}:
        doc["status"] = "in_progress"
        doc["audit"] = None


def sync_contract_revisions(catalog: dict, docs: list[dict]) -> list[str]:
    """Refresh catalog-owned metadata on kept documents and demote written
    documents whose content-contract revision drifted (so a revise run
    re-grounds them even when source provenance is FRESH)."""
    contract_updated: list[str] = []
    for doc in docs:
        catalog_id = catalog_id_for_document(catalog, doc)
        if catalog_id is None:
            continue
        detail = query_catalog.load_type(catalog_id)
        doc["title"] = detail.get("title") or doc["title"]
        doc["description"] = detail.get("summary") or doc.get("description", "")
        doc["scaffold_template"] = detail["template_file"]
        doc["instruction_file"] = detail.get("instruction_file")
        doc["target_depth"] = detail.get("target_depth", doc["target_depth"])
        doc["write_order"] = detail.get("write_order", doc["write_order"])
        if detail.get("nav_order") is not None:
            doc["nav_order"] = detail["nav_order"]
        doc["audit_profile"] = detail.get("audit_profile", doc["audit_profile"])
        doc["requires"] = list(detail.get("requires", doc.get("requires", [])))
        revision = detail.get("contract_revision")
        if revision is not None and doc.get("contract_revision") != revision:
            doc["contract_revision"] = revision
            demote_written(doc)
            contract_updated.append(doc["id"])
    return contract_updated


def sync_presentations(catalog: dict, docs: list[dict], audiences: list[str]) -> list[str]:
    """Hydrate legacy manifests and invalidate only changed reader-facing output."""
    updated: list[str] = []
    for doc in docs:
        catalog_id = catalog_id_for_document(catalog, doc)
        if catalog_id is None:
            continue
        resolved = effective_presentation(
            catalog_id,
            audiences,
            doc.get("presentation_override"),
        )
        if "presentation" not in doc:
            doc["presentation"] = resolved
            continue
        if doc["presentation"] != resolved:
            doc["presentation"] = resolved
            demote_written(doc)
            updated.append(doc["id"])
    return updated


def sync_dominant_forms(catalog: dict, docs: list[dict]) -> list[str]:
    """Hydrate the catalog's `dominant_form` and demote written documents
    whose declared form changed, so the illustration gate and the writer
    brief read one value."""
    updated: list[str] = []
    for doc in docs:
        catalog_id = catalog_id_for_document(catalog, doc)
        if catalog_id is None:
            continue
        declared = query_catalog.load_type(catalog_id).get("dominant_form")
        if "dominant_form" not in doc:
            doc["dominant_form"] = declared
            continue
        if doc["dominant_form"] != declared:
            doc["dominant_form"] = declared
            demote_written(doc)
            updated.append(doc["id"])
    return updated


def relayout_dynamic_documents(
    catalog: dict,
    documents: list[dict],
    selected: list[dict],
    old_layout: str,
    new_layout: str,
    audiences: list[str],
) -> tuple[list[dict], set[str]]:
    """Move discovered instances across a layout switch, so neither direction
    loses one. Returns `(extra_documents, folded_ids)`.

    **compact -> standard**: every `{id, slug, title}` section on a merged
    entry becomes a dynamic document again, at the type's own path with the
    section's slug. Without this the merged entry is dropped as unselected and
    takes its sections with it.

    **standard -> compact**: every dynamic document whose type declares a
    `compact_group` present in the new selection becomes a section on that
    group's merged entry, and its id is returned so the caller retires or
    removes the standalone document. Instances past `COMPACT_DYNAMIC_CAP` keep
    their own file rather than being dropped — a section budget must never
    silently discard written work."""
    if old_layout == new_layout:
        return [], set()
    by_catalog_id = {item["id"]: item for item in catalog["documents"]}
    if new_layout == "standard":
        extra: list[dict] = []
        taken = {doc["id"] for doc in documents} | {doc["id"] for doc in selected}
        for doc in documents:
            for member in doc.get("compact_members") or []:
                if not isinstance(member, dict):
                    continue
                definition = by_catalog_id.get(member["id"])
                if definition is None:
                    continue
                slug = member["slug"]
                doc_id = slug if slug not in taken else f"{member['id']}_{slug}"
                taken.add(doc_id)
                actual = dict(definition)
                actual["id"] = doc_id
                actual["path"] = definition["path"].replace("{slug}", slug)
                actual["title"] = member.get("title") or slug
                extra.append(make_document(
                    actual,
                    [{"kind": "dynamic", "id": definition["type"]}],
                    catalog_id=definition["id"],
                    audiences=audiences,
                ))
        return extra, set()

    merged_by_group = {
        doc["id"]: doc for doc in selected if isinstance(doc.get("compact_members"), list)
    }
    folded: set[str] = set()
    for doc in documents:
        origins = doc.get("selection", {}).get("origins", [])
        if not any(origin.get("kind") == "dynamic" for origin in origins):
            continue
        catalog_id = catalog_id_for_document(catalog, doc)
        if catalog_id is None:
            continue
        group_id = query_catalog.load_type(catalog_id).get("compact_group")
        merged = merged_by_group.get(group_id) if group_id else None
        if merged is None:
            continue
        sections = [item for item in merged["compact_members"] if isinstance(item, dict)]
        if len([item for item in sections if item["id"] == catalog_id]) >= query_catalog.COMPACT_DYNAMIC_CAP:
            continue
        merged["compact_members"].append({
            "id": catalog_id,
            "slug": section_slug(doc["path"]),
            "title": doc.get("title") or section_slug(doc["path"]),
        })
        merged["requires"] = sorted(set(merged.get("requires", [])) | set(doc.get("requires", [])))
        folded.add(doc["id"])
    return [], folded


def cmd_reconcile(args: argparse.Namespace) -> int:
    """Apply the revise question pack answers to an existing manifest.

    Updates tier and the five profile dimensions from the user's selection,
    re-runs static selection, adds newly applicable documents as planned,
    removes planned documents that are no longer applicable, and preserves
    written, skipped, and dynamic documents. An explicit `none` value clears a
    dimension; an omitted dimension keeps its current manifest value.
    """
    try:
        manifest = load_manifest(
            manifest_path(args.repo),
            unsupported_hint=MANIFEST_HINT,
        )
    except ValueError as exc:
        return fail(str(exc), 2)
    catalog = load_catalog()
    new_tier = args.tier or manifest["project"]["tier"]
    project = manifest["project"]
    current_scale = project.get("scale") or {}
    requested_layout = (
        args.layout
        or (scale.LAYOUT_BY_CLASS[args.scale_class] if args.scale_class else None)
        or current_scale.get("layout", "standard")
    )
    # Moving to portfolio drops a compact manifest to standard; the folded
    # members return as planned and the merged entry becomes a retire
    # candidate through the ordinary compact->standard path below.
    try:
        new_layout, layout_constraint = scale.layout_for(
            new_tier, requested_layout, explicit=args.layout is not None
        )
    except scale.LayoutTierError as exc:
        return fail(str(exc), 2)
    raw: dict[str, list[str]] = {}
    for dimension in PROFILE_DIMENSIONS:
        singular = "audience" if dimension == "audiences" else dimension[:-1]
        values = list(getattr(args, singular, []) or [])
        raw[dimension] = [] if values == ["none"] else (values or manifest["project"]["profiles"].get(dimension, []))
    try:
        profiles = normalize_profiles(catalog, raw)
    except ValueError as exc:
        return fail(str(exc), 2)
    # Omitted --group keeps the stored scope, exactly like every other
    # dimension flag; `--group none` clears it back to every group.
    requested_groups = list(getattr(args, "group", []) or [])
    try:
        if requested_groups == ["none"]:
            new_groups: list[str] = []
        elif requested_groups:
            new_groups = query_catalog.normalize_groups(requested_groups)
        else:
            new_groups = list(manifest["project"].get("groups", []))
    except ValueError as exc:
        return fail(str(exc), 2)
    selected = selected_static_documents(
        catalog, args.repo, new_tier, profiles, layout=new_layout, groups=new_groups,
    )
    if not selected:
        return fail(empty_selection_message(new_groups, profiles), 2)
    selected_ids = {doc["id"] for doc in selected}
    relaid_out, folded_away = relayout_dynamic_documents(
        catalog,
        manifest["documents"],
        selected,
        current_scale.get("layout", "standard"),
        new_layout,
        profiles["audiences"],
    )
    kept: list[dict] = []
    removed: list[str] = []
    retire: list[str] = []
    kept_ids: set[str] = set()
    for doc in manifest["documents"]:
        origins = doc.get("selection", {}).get("origins", [])
        is_dynamic = any(origin.get("kind") == "dynamic" for origin in origins)
        if doc["id"] in folded_away:
            # Its subject now lives as a `##` in the merged file. A written
            # file still has prose to migrate, so it retires rather than
            # vanishing; a planned one just drops out of the plan.
            if doc.get("status") in WRITTEN:
                retire.append(doc["id"])
                kept.append(doc)
                kept_ids.add(doc["id"])
            else:
                removed.append(doc["id"])
            continue
        if doc["id"] in selected_ids:
            if doc.get("status") == "retired":
                doc["status"] = "planned"
                doc["audit"] = None
                doc.pop("retired_at", None)
                doc.pop("retired_destination", None)
            kept.append(doc)
            kept_ids.add(doc["id"])
        elif is_dynamic or doc.get("status") != "planned":
            if not is_dynamic and doc.get("status") in WRITTEN:
                retire.append(doc["id"])
            kept.append(doc)
            kept_ids.add(doc["id"])
        else:
            removed.append(doc["id"])
    added = [doc for doc in selected if doc["id"] not in kept_ids]
    added += [doc for doc in relaid_out if doc["id"] not in kept_ids]
    contract_updated = sync_contract_revisions(catalog, kept)
    presentation_updated = sync_presentations(catalog, kept, profiles["audiences"])
    form_updated = sync_dominant_forms(catalog, kept)
    old_tier = manifest["project"]["tier"]
    manifest["documents"] = kept + added
    manifest["documents"].sort(key=lambda item: (item["write_order"], item["path"], item["id"]))
    manifest["project"]["tier"] = new_tier
    manifest["project"]["profiles"] = profiles
    if new_groups:
        manifest["project"]["groups"] = new_groups
    else:
        manifest["project"].pop("groups", None)
    tier_forced_layout = layout_constraint == "tier-constraint"
    if args.scale_class or args.layout or tier_forced_layout:
        if current_scale.get("class"):
            scale_record = dict(current_scale)
        else:
            # A pre-3.5 manifest reconciled before migrate has no usable prior
            # record. Detect a complete one rather than emit a record missing
            # the schema-required `class`.
            scale_record = resolve_scale(args.repo, args.scale_class, args.layout)
        old_class = scale_record.get("class")
        old_layout = scale_record.get("layout", "standard")
        if args.scale_class and args.scale_class != old_class:
            scale_record["class"] = args.scale_class
            # A class change carries its class-default layout unless the user
            # also named a layout.
            if not args.layout:
                scale_record["layout"] = scale.LAYOUT_BY_CLASS[args.scale_class]
        if args.layout and args.layout != old_layout:
            scale_record["layout"] = args.layout
        if tier_forced_layout:
            # The tier overrides whatever layout the flags or the manifest
            # implied; record that as the reason rather than as a user pick.
            scale_record["layout"] = new_layout
        scale_record["decided_by"] = "tier-constraint" if tier_forced_layout else "user"
        scale_record["decided_at"] = now_iso()
        detected = scale.compute_scale(args.repo)
        scale_record["detected_class"] = detected["class"]
        scale_record["signals"] = detected["signals"]
        manifest["project"]["scale"] = scale_record
        if old_class != scale_record.get("class"):
            print(f"  scale class: {old_class} -> {scale_record['class']}")
        if old_layout != scale_record.get("layout"):
            print(f"  layout: {old_layout} -> {scale_record['layout']}")
    save_manifest(args.repo, manifest)
    print(f"Reconcile {args.repo}:")
    print(f"  tier: {old_tier} -> {new_tier}")
    for dimension in PROFILE_DIMENSIONS:
        print(f"  {dimension}: {', '.join(profiles[dimension]) or '(none)'}")
    count_parts = []
    if added:
        count_parts.append(f"{len(added)} add")
    if removed:
        count_parts.append(f"{len(removed)} removed-planned")
    if retire:
        count_parts.append(f"{len(retire)} retire")
    if contract_updated:
        count_parts.append(f"{len(contract_updated)} contract-updated")
    if presentation_updated:
        count_parts.append(f"{len(presentation_updated)} presentation-updated")
    if form_updated:
        count_parts.append(f"{len(form_updated)} dominant-form-updated")
    print(f"  counts: {', '.join(count_parts) or 'no change'}")
    if added:
        print(f"  added: {', '.join(doc['id'] for doc in sorted(added, key=lambda d: d['id']))}")
    if removed:
        print(f"  removed-planned: {', '.join(sorted(removed))}")
    if retire:
        print(f"  retire: {', '.join(sorted(retire))} (written, out of scope — approve the retire step to move or delete)")
    if contract_updated:
        print(f"  contract-updated: {', '.join(sorted(contract_updated))}")
    if presentation_updated:
        print(f"  presentation-updated: {', '.join(sorted(presentation_updated))}")
    if form_updated:
        print(f"  dominant-form-updated: {', '.join(sorted(form_updated))}")
    print(f"  kept: {len(kept)} documents")
    print()
    for line in plan_lines(args.repo, manifest, args.repo / ".docforge" / "flow-index.json", revise=True):
        print(line)
    return 0


def find_document(manifest: dict, doc_id: str) -> dict:
    for doc in manifest["documents"]:
        if doc["id"] == doc_id:
            return doc
    raise ValueError(f"document id not found: {doc_id}")


def cmd_set(args: argparse.Namespace) -> int:
    try:
        manifest = load_manifest(
            manifest_path(args.repo),
            unsupported_hint=MANIFEST_HINT,
        )
        doc = find_document(manifest, args.id)
    except ValueError as exc:
        return fail(str(exc), 2)
    old = doc["status"]
    if args.status == old:
        print(f"{args.id}: {old} -> {args.status}")
        return 0
    if args.status not in TRANSITIONS.get(old, set()):
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


def cmd_presentation(args: argparse.Namespace) -> int:
    try:
        manifest = load_manifest(manifest_path(args.repo), unsupported_hint=MANIFEST_HINT)
        doc = find_document(manifest, args.id)
        catalog = load_catalog()
        catalog_id = catalog_id_for_document(catalog, doc)
        if catalog_id is None:
            raise ValueError(f"catalog definition not found for document: {args.id}")
    except ValueError as exc:
        return fail(str(exc), 2)

    if (
        doc.get("group") == AGENT_CONTEXT_GROUP
        and args.related_docs not in {None, "none"}
    ):
        return fail("agent-context documents require --related-docs none", 2)

    if args.reset:
        if any((args.primary_audience, args.code, args.related_docs, args.repository_paths)):
            return fail("--reset cannot be combined with presentation values", 2)
        doc.pop("presentation_override", None)
    else:
        override = {
            key: value
            for key, value in {
                "primary_audience": args.primary_audience,
                "code": args.code,
                "related_docs": args.related_docs,
                "repository_paths": args.repository_paths,
            }.items()
            if value is not None
        }
        if not override:
            return fail("set at least one presentation value or pass --reset", 2)
        audience_ids = {item["id"] for item in catalog["profiles"]["audiences"]}
        if "primary_audience" in override and override["primary_audience"] not in audience_ids:
            return fail(f"unknown audience: {override['primary_audience']}", 2)
        for field, allowed in query_catalog.PRESENTATION_VALUES.items():
            if field in override and override[field] not in allowed:
                return fail(f"invalid {field}: {override[field]}", 2)
        doc["presentation_override"] = {**doc.get("presentation_override", {}), **override}

    resolved = effective_presentation(
        catalog_id,
        manifest["project"]["profiles"]["audiences"],
        doc.get("presentation_override"),
    )
    changed = doc.get("presentation") != resolved
    doc["presentation"] = resolved
    if changed:
        demote_written(doc)
    save_manifest(args.repo, manifest)
    print(f"Presentation {args.id}: {'updated' if changed else 'unchanged'}.")
    return 0


def cmd_audit(args: argparse.Namespace) -> int:
    try:
        manifest = load_manifest(
            manifest_path(args.repo),
            unsupported_hint=MANIFEST_HINT,
        )
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
        manifest = load_manifest(
            manifest_path(args.repo),
            unsupported_hint=MANIFEST_HINT,
        )
    except ValueError as exc:
        return fail(str(exc), 2)
    project = manifest["project"]
    print(f"repo: {project['name']}  tier: {project['tier']}")
    for dimension in PROFILE_DIMENSIONS:
        values = ", ".join(project["profiles"][dimension]) or "none"
        print(f"  {dimension}: {values}")
    graph = manifest.get("graph")
    if graph:
        print(f"  graph: {graph['provider']} (flow: {graph['flow']})")
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
        f"complete={counts['complete']} skipped={counts['skipped']} "
        f"retired={counts.get('retired', 0)}"
    )
    return 0


def cmd_set_graph(args: argparse.Namespace) -> int:
    try:
        manifest = load_manifest(manifest_path(args.repo), unsupported_hint=MANIFEST_HINT)
    except ValueError as exc:
        return fail(str(exc), 2)
    try:
        lock = resolve_graph_lock(args.repo, args.provider)
    except ValueError as exc:
        return fail(str(exc), 2)
    if lock is None:
        return fail("no graph provider is ready in this repo", 2)
    existing = manifest.get("graph")
    if existing and existing["provider"] != lock["provider"] and not args.force:
        return fail(
            f"graph provider is locked to {existing['provider']} for this session "
            f"(locked_at {existing['locked_at']}); pass --force to relock to {lock['provider']}",
            2,
        )
    verb = "Locked"
    if existing:
        verb = "Updated" if existing["provider"] == lock["provider"] else "Relocked"
        if existing["provider"] == lock["provider"]:
            lock["locked_at"] = existing["locked_at"]
    manifest["graph"] = lock
    save_manifest(args.repo, manifest)
    print(f"{verb} graph provider: {lock['provider']} (flow: {lock['flow']})")
    return 0


def cmd_finish(args: argparse.Namespace) -> int:
    docforge_dir = args.repo / ".docforge"
    if not docforge_dir.is_dir():
        return fail(f".docforge directory not found: {docforge_dir}", 2)
    result = finish_docforge(docforge_dir, clean_tmp=not args.keep_tmp)
    cleaned = ", ".join(result["cleaned_dirs"]) if result["cleaned_dirs"] else "none"
    print(f"finish  ensured {docforge_dir / '.gitignore'}")
    print(f"finish  cleaned ephemeral scratch dirs: {cleaned}")
    return 0


UNMANAGED_ROOTS = ("docs/", "docs-portfolio/")


def unmanaged_source(path: PurePosixPath) -> PurePosixPath:
    """The docs root (`docs` / `docs-portfolio`) an unmanaged path lives
    under, or None when it is outside the docs tree."""
    for root in UNMANAGED_ROOTS:
        prefix = PurePosixPath(root.rstrip("/"))
        try:
            relative = path.relative_to(prefix)
        except ValueError:
            continue
        if relative.parts and relative.name.endswith((".md", ".mdx")):
            return prefix
    return None


def validate_unmanaged_path(repo: Path, value: str) -> PurePosixPath:
    """A safe, existing, markdown path under the docs tree, not owned by any
    manifest document. Returns the normalized relative path."""
    validate_relative_path(value)
    relative = PurePosixPath(value)
    root = unmanaged_source(relative)
    if root is None:
        raise ValueError(
            f"unmanaged path must be a .md/.mdx file under {' or '.join(UNMANAGED_ROOTS)}: {value}"
        )
    if not (repo / relative).is_file():
        raise ValueError(f"file not found: {value}")
    return relative


def unmanaged_entries(manifest: dict) -> list[dict]:
    return manifest["project"]["unmanaged_docs"]


def cmd_unmanaged(args: argparse.Namespace) -> int:
    try:
        manifest = load_manifest(manifest_path(args.repo), unsupported_hint=MANIFEST_HINT)
    except ValueError as exc:
        return fail(str(exc), 2)
    entries = unmanaged_entries(manifest)
    by_path = {entry["path"]: entry for entry in entries}
    action = args.action
    if action == "list":
        if not entries:
            print("unmanaged  none")
            return 0
        for entry in entries:
            print(f"unmanaged  {entry['path']}  (since {entry['decided_at']})")
        return 0
    if not args.path:
        return fail(f"unmanaged {action} requires --path", 2)
    tracked = {doc["path"] for doc in manifest.get("documents", []) if doc.get("path")}
    if action in {"add", "archive"}:
        try:
            relative = validate_unmanaged_path(args.repo, args.path)
        except ValueError as exc:
            return fail(str(exc), 2)
        value = relative.as_posix()
        if value in tracked:
            return fail(f"{value} is a tracked manifest document; unmanaged is for docs Docforge does not own", 2)
        if action == "add":
            if value in by_path:
                print(f"unmanaged  {value} already self-managed; no changes.")
                return 0
            entries.append({"path": value, "decided_at": now_iso()})
            save_manifest(args.repo, manifest)
            print(f"unmanaged  {value} -> self-managed (never tracked, never re-asked)")
            return 0
        archived = PurePosixPath("docs") / "_archive" / str(datetime.now(timezone.utc).year)
        if relative.parts and relative.parts[0] == "docs-portfolio":
            archived = PurePosixPath("docs-portfolio") / "_archive" / str(datetime.now(timezone.utc).year)
        target = archived / PurePosixPath(*relative.parts[1:])
        if args.dry_run:
            print(f"DRY RUN  move {value} -> {target.as_posix()}")
            return 0
        if (args.repo / target).exists():
            return fail(f"archive target already exists: {target.as_posix()}", 2)
        (args.repo / target).parent.mkdir(parents=True, exist_ok=True)
        (args.repo / value).rename(args.repo / target)
        entries.append({"path": target.as_posix(), "decided_at": now_iso()})
        save_manifest(args.repo, manifest)
        print(f"unmanaged  {value} -> {target.as_posix()} (archived)")
        return 0
    if action == "remove":
        value = args.path
        if value not in by_path:
            print(f"unmanaged  {value} not in list; no changes.")
            return 0
        entries[:] = [entry for entry in entries if entry["path"] != value]
        save_manifest(args.repo, manifest)
        print(f"unmanaged  {value} -> removed from list (file untouched)")
        return 0
    return fail(f"unknown unmanaged action: {action}", 2)


def cmd_retire(args: argparse.Namespace) -> int:
    """Move out-of-scope written documents to a git-ignored obsolete location
    (default) or delete them, marking the manifest entry `retired` — the entry
    itself is always preserved. A file operation: never under `--auto-accept`,
    always an explicitly approved step after `reconcile` reports the delta."""
    try:
        manifest = load_manifest(manifest_path(args.repo), unsupported_hint=MANIFEST_HINT)
    except ValueError as exc:
        return fail(str(exc), 2)
    year = str(datetime.now(timezone.utc).year)
    if not args.dry_run:
        ensure_docforge_gitignore(args.repo / ".docforge")
    moved_any = False
    for doc_id in args.doc:
        try:
            doc = find_document(manifest, doc_id)
        except ValueError as exc:
            return fail(str(exc), 2)
        if doc.get("status") == "retired":
            print(f"retire  {doc_id}: already retired; no changes.")
            continue
        if doc.get("status") not in WRITTEN:
            return fail(f"{doc_id} has status {doc.get('status')}; only written documents can be retired", 2)
        value = PurePosixPath(doc["path"])
        if args.mode == "obsolete":
            target = PurePosixPath(".docforge") / "obsolete" / year / value
            label = f"move {value.as_posix()} -> {target.as_posix()}"
            if args.dry_run:
                print(f"DRY RUN  retire {doc_id}: {label}")
                continue
            source = args.repo / value
            if not source.is_file():
                return fail(f"file not found: {value.as_posix()}", 2)
            destination = args.repo / target
            if destination.exists():
                return fail(f"retire target already exists: {target.as_posix()}", 2)
            destination.parent.mkdir(parents=True, exist_ok=True)
            ensure_gitignored_dir(args.repo / ".docforge" / "obsolete" / year)
            source.rename(destination)
            doc["retired_destination"] = target.as_posix()
        else:
            label = f"delete {value.as_posix()}"
            if args.dry_run:
                print(f"DRY RUN  retire {doc_id}: {label}")
                continue
            source = args.repo / value
            if source.is_file():
                source.unlink()
        doc["retired_at"] = now_iso()
        doc["status"] = "retired"
        doc["audit"] = None
        moved_any = True
        print(f"retire  {doc_id}: {label} (status -> retired; entry preserved)")
    if not args.dry_run and moved_any:
        save_manifest(args.repo, manifest)
    return 0


def _selection_values(args: argparse.Namespace) -> list[tuple[str, str]]:
    """The `(dimension, value)` pairs this invocation actually selected."""
    pairs = []
    for dimension, singular in (
        ("shapes", "shape"), ("platforms", "platform"), ("frameworks", "framework"),
        ("concerns", "concern"), ("audiences", "audience"),
    ):
        for value in getattr(args, singular, []) or []:
            pairs.append((dimension, value))
    return pairs


def cmd_preview(args: argparse.Namespace) -> int:
    """Report how large a tree a scope would produce, without writing anything.

    Intake needs this before the confirmation gate: a user picking profiles and
    audiences has no way to know that most dimensions cost nothing while one
    audience can carry a third of the tree. Read-only — no manifest, no
    directories, no side effects of any kind."""
    catalog = load_catalog()
    selected = {
        "shapes": args.shape, "platforms": args.platform,
        "frameworks": args.framework, "concerns": args.concern,
        "audiences": args.audience or ["engineers", "beginners"],
    }
    try:
        profiles = normalize_profiles(catalog, selected)
    except ValueError as exc:
        return fail(str(exc), 2)
    try:
        scoped_groups = query_catalog.normalize_groups(list(getattr(args, "group", []) or []))
    except ValueError as exc:
        return fail(str(exc), 2)

    def documents(layout: str, drop: tuple[str, str] | None = None) -> list[dict]:
        trimmed = dict(profiles)
        if drop is not None:
            dimension, value = drop
            trimmed[dimension] = [v for v in profiles[dimension] if v != value]
        return selected_static_documents(
            catalog, args.repo, args.tier, trimmed, layout=layout, groups=scoped_groups
        )

    def count(layout: str, drop: tuple[str, str] | None = None) -> int:
        return len(documents(layout, drop))

    standard_count = count("standard")
    report: dict = {"tier": args.tier, "standard_count": standard_count}
    report["groups"] = scoped_groups
    try:
        compact_layout, _ = scale.layout_for(args.tier, "compact", explicit=True)
    except scale.LayoutTierError as exc:
        report["compact_count"] = None
        report["compact_unavailable"] = str(exc)
    else:
        report["compact_count"] = count(compact_layout)

    # Ablation, not origin-counting: "how many documents disappear if this
    # value is dropped" is the number a user weighing a choice actually wants,
    # and it stays correct when several selections claim the same document.
    layout = args.layout or ("compact" if report.get("compact_count") is not None else "standard")
    if layout == "compact" and report.get("compact_count") is None:
        layout = "standard"
    projected = documents(layout)
    baseline = len(projected)
    report["layout"] = layout
    report["count"] = baseline
    attribution = []
    for dimension, value in _selection_values(args):
        canonical = [v for v in profiles[dimension]]
        if value not in canonical:
            continue
        attribution.append({
            "dimension": dimension,
            "value": value,
            "documents": baseline - count(layout, drop=(dimension, value)),
        })
    attribution.sort(key=lambda item: (-item["documents"], item["dimension"], item["value"]))
    report["attribution"] = attribution

    # Compact trades files for sections, so a file count alone hides how dense
    # the result is. Report the densest merged files, and name any group that
    # spilled past the section cap — a spilled group keeps standard-layout
    # children, which is the one case where compact stops being bounded.
    if layout == "compact":
        merged = [
            doc for doc in selected_static_documents(
                catalog, args.repo, args.tier, profiles,
                layout="compact", groups=scoped_groups,
            )
            if doc.get("compact_members")
        ]
        report["sections"] = sorted(
            ({"path": doc["path"], "sections": len(doc["compact_members"])} for doc in merged),
            key=lambda item: (-item["sections"], item["path"]),
        )
        report["spilled"] = sorted(
            item["path"] for item in report["sections"]
            if item["sections"] >= query_catalog.COMPACT_SECTION_CAP
        )

    if args.json:
        print(dump_json(report), end="")
        return 0
    print(f"Preview {args.repo} — tier: {args.tier}")
    if report["compact_count"] is None:
        print(f"  standard: {standard_count} documents")
        print(f"  compact:  unavailable — {report['compact_unavailable']}")
    else:
        print(f"  standard: {standard_count} documents")
        print(f"  compact:  {report['compact_count']} documents")
    print(f"  projected ({layout}): {baseline} documents")
    if attribution:
        print("  attribution (documents lost if the value is dropped):")
        for item in attribution:
            share = f" — {round(100 * item['documents'] / baseline)}% of the tree" if baseline and item["documents"] else ""
            print(f"    {item['dimension'][:-1]}={item['value']}: {item['documents']}{share}")
    for item in report.get("sections", [])[:3]:
        print(f"  densest: {item['path']} — {item['sections']} sections")
    for path in report.get("spilled", []):
        print(
            f"  spilled: {path} reached the {query_catalog.COMPACT_SECTION_CAP}-section "
            "cap; the overflow keeps its own standard paths"
        )
    print("  (read-only: nothing was written)")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    def add_repo(command: argparse.ArgumentParser) -> None:
        command.add_argument("--repo", required=True, type=Path)

    init = sub.add_parser("init")
    add_repo(init)
    init.add_argument("--tier", required=True, choices=["spine", "diligence", "portfolio"])
    init.add_argument("--scale-class", choices=["small", "medium", "large"])
    init.add_argument("--layout", choices=["compact", "standard"])
    init.add_argument("--shape", action="append", default=[])
    init.add_argument("--platform", action="append", default=[])
    init.add_argument("--framework", action="append", default=[])
    init.add_argument("--concern", action="append", default=[])
    init.add_argument("--audience", action="append", default=[])
    init.add_argument(
        "--group", action="append", default=[],
        help="Restrict this run to these catalog groups (repeatable, aliases accepted). Omit for every group.",
    )
    init.add_argument("--overlay", dest="obsolete_overlay", action="append", default=[], help=argparse.SUPPRESS)
    init.add_argument("--name")
    init.add_argument("--force", action="store_true")
    init.add_argument("--graph-provider")
    init.set_defaults(func=cmd_init)

    preview = sub.add_parser("preview")
    add_repo(preview)
    preview.add_argument("--tier", required=True, choices=["spine", "diligence", "portfolio"])
    preview.add_argument("--layout", choices=["compact", "standard"])
    preview.add_argument("--scale-class", choices=["small", "medium", "large"])
    preview.add_argument("--shape", action="append", default=[])
    preview.add_argument("--platform", action="append", default=[])
    preview.add_argument("--framework", action="append", default=[])
    preview.add_argument("--concern", action="append", default=[])
    preview.add_argument("--audience", action="append", default=[])
    preview.add_argument(
        "--group", action="append", default=[],
        help="Project the tree for these catalog groups only (repeatable, aliases accepted).",
    )
    preview.add_argument("--json", action="store_true")
    preview.set_defaults(func=cmd_preview)

    add = sub.add_parser("add")
    add_repo(add)
    add.add_argument("--type", required=True)
    add.add_argument("--id", required=True)
    add.add_argument("--path", required=True)
    add.add_argument("--title")
    add.add_argument("--evidence", action="append", default=[])
    add.set_defaults(func=cmd_add)

    set_status = sub.add_parser("set")
    add_repo(set_status)
    set_status.add_argument("--id", required=True)
    set_status.add_argument("--status", required=True, choices=STATUSES)
    set_status.set_defaults(func=cmd_set)

    presentation = sub.add_parser("presentation")
    add_repo(presentation)
    presentation.add_argument("--id", required=True)
    presentation.add_argument("--primary-audience")
    presentation.add_argument("--code", choices=sorted(query_catalog.PRESENTATION_VALUES["code"]))
    presentation.add_argument("--related-docs", choices=sorted(query_catalog.PRESENTATION_VALUES["related_docs"]))
    presentation.add_argument("--repository-paths", choices=sorted(query_catalog.PRESENTATION_VALUES["repository_paths"]))
    presentation.add_argument("--reset", action="store_true")
    presentation.set_defaults(func=cmd_presentation)

    audit = sub.add_parser("audit")
    add_repo(audit)
    audit.add_argument("--id", required=True)
    audit.add_argument("--mode", required=True, choices=["cold-pass"])
    audit.add_argument("--verdict", required=True, choices=["PASS", "FAIL"])
    audit.add_argument("--report", required=True)
    audit.set_defaults(func=cmd_audit)

    status = sub.add_parser("status")
    add_repo(status)
    status.set_defaults(func=cmd_status)

    set_graph = sub.add_parser("set-graph")
    add_repo(set_graph)
    set_graph.add_argument("--provider")
    set_graph.add_argument("--force", action="store_true")
    set_graph.set_defaults(func=cmd_set_graph)

    reconcile = sub.add_parser("reconcile")
    add_repo(reconcile)
    reconcile.add_argument("--tier", choices=["spine", "diligence", "portfolio"])
    reconcile.add_argument("--scale-class", choices=["small", "medium", "large"])
    reconcile.add_argument("--layout", choices=["compact", "standard"])
    reconcile.add_argument("--shape", action="append", default=[])
    reconcile.add_argument("--platform", action="append", default=[])
    reconcile.add_argument("--framework", action="append", default=[])
    reconcile.add_argument("--concern", action="append", default=[])
    reconcile.add_argument("--audience", action="append", default=[])
    reconcile.add_argument(
        "--group", action="append", default=[],
        help="Replace the stored group scope (repeatable). Omit to keep the manifest's current scope.",
    )
    reconcile.set_defaults(func=cmd_reconcile)

    unmanaged = sub.add_parser("unmanaged")
    add_repo(unmanaged)
    unmanaged.add_argument(
        "--action", required=True, choices=["list", "add", "remove", "archive"],
        help="list self-managed docs, or add/remove/archive one (archive moves it into docs/_archive/<year>/)",
    )
    unmanaged.add_argument("--path", help="repository-relative path of the unmanaged doc")
    unmanaged.add_argument("--dry-run", action="store_true")
    unmanaged.set_defaults(func=cmd_unmanaged)

    retire = sub.add_parser("retire")
    add_repo(retire)
    retire.add_argument(
        "--doc", action="append", required=True,
        help="manifest document id to retire (repeatable)",
    )
    retire.add_argument(
        "--mode", required=True, choices=["obsolete", "delete"],
        help="obsolete: move to .docforge/obsolete/<year>/; delete: remove the file",
    )
    retire.add_argument("--dry-run", action="store_true")
    retire.set_defaults(func=cmd_retire)

    finish = sub.add_parser("finish")
    add_repo(finish)
    finish.add_argument("--keep-tmp", action="store_true", help="Do not clean up tmp/ and scratch/")
    finish.set_defaults(func=cmd_finish)

    return parser


def main() -> int:
    args = build_parser().parse_args()
    if not args.repo.is_dir():
        return fail(f"not a directory: {args.repo}", 2)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
