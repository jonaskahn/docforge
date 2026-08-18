#!/usr/bin/env python3
"""Preview, materialize, or audit the exact tree in a Docforge manifest."""

from __future__ import annotations

import argparse
import json
import posixpath
import re
import sys
from pathlib import Path, PurePosixPath

from runtime.common.python._util import ensure_docforge_gitignore, fail, load_manifest, unmanaged_paths
from runtime.common.python.agent_context import (
    AGENT_CONTEXT_GROUP,
    agent_context_leaks,
    agent_context_outbound_findings,
)
from runtime.common.python.plan import plan_entries
from runtime.common.python.markdown_fences import scan_fences
from runtime.common.python.repo_identity import identity_of
from runtime.common.python.special_files import SPECIAL_DOC_OUTPUTS
from runtime.common.python.provenance_frontmatter import (
    BLOB,
    FLOW_VALUES,
    PROVENANCE_FIELDS,
    SCAFFOLD_TOKEN,
    SOURCE_ROLES,
    SUPPORTED_SCHEMA_VERSIONS,
    parse_frontmatter as codec_parse_frontmatter,
    scaffold_provenance as build_provenance,
)
from runtime.common.python import provenance_store as store
from runtime.catalog.python import query_catalog

SKILL_ROOT = Path(__file__).resolve().parent.parent.parent.parent
PLACEHOLDER = re.compile(r"\{\{[^}]+\}\}|TODO\([^)]*\)")
TOKEN = re.compile(r"<[A-Z][A-Z0-9_]{2,}>")
LINK = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
FORGE = re.compile(
    r"\b(github|gitlab|bitbucket|gitea|forgejo|sourcehut|azure devops|"
    r"github actions|gitlab ci|codeowners)\b",
    re.IGNORECASE,
)
MARKDOWN_EXCEPTIONS = SPECIAL_DOC_OUTPUTS
WRITTEN = {"generated", "needs_review", "complete"}
SCALAR_PROVENANCE_FIELDS = PROVENANCE_FIELDS - {"graph", "sections", "generator"}
INDEX_TYPES = {
    "folder-index", "docs-index", "portfolio-index", "portfolio-decisions-index",
    "ba-index", "po-index", "decision-index", "flow-index",
}
# A merged compact file replaces its folder's index and inherits its routing
# duty; it is not in INDEX_TYPES because it is not otherwise an index.
COMPACT_TYPE = "compact-doc"
CHILDREN_START = "<!-- docforge-children:start -->"
CHILDREN_END = "<!-- docforge-children:end -->"
# Each index template carries its own table header inside the managed markers,
# and the templates disagree on width (2 columns for a section README, 5 for
# the decision log, 8 for the flow index). Regenerating the block has to
# re-emit that header: rows alone render as literal pipe text, not a table.
TABLE_SEPARATOR = re.compile(r"^\|(?:\s*:?-{3,}:?\s*\|)+$")
# Folders whose contents are dynamically discovered, mapped to whether the
# collection root itself must hold a child.
#
# `docs/flows/` is exempt at the root: its index is a discovery report that
# also records deferred, placeholder, and skipped candidates, so it earns its
# place with no promoted flow. Every other collection index is pure routing --
# with no child it is a promise the tree never keeps, which is how `concepts/`,
# `decisions/`, and `runbooks/` shipped holding nothing but an index explaining
# its own emptiness, in two separate repositories, with the audit recording
# PASS. Family subfolders are checked under every prefix.
COLLECTION_PREFIXES = {
    "docs/flows/": False,
    "docs/architecture/concepts/": True,
    "docs/architecture/decisions/": True,
    "docs/architecture/contracts/": True,
    "docs/operations/runbooks/": True,
    "docs/product/migrations/": True,
    "docs-portfolio/epics/": True,
    "docs-portfolio/decisions/": True,
}


def resolve_manifest(value: Path, repo: Path) -> Path:
    if value.is_absolute():
        return value
    direct = value.resolve()
    repo_relative = (repo / value).resolve()
    return direct if direct.exists() else repo_relative


def active_documents(manifest: dict) -> list[dict]:
    return [doc for doc in manifest["documents"] if doc.get("status") not in {"skipped", "retired"}]


def routable_children(doc: dict, manifest: dict) -> list[dict]:
    """Children a router may enumerate; agent outputs are never routing rows.

    This keeps human indexes isolated and prevents a legacy agent index from
    enumerating peer agent outputs. Entries without a group predate the field
    and remain human-facing."""
    return [
        child
        for child in active_documents(manifest)
        if child.get("group") != AGENT_CONTEXT_GROUP
    ]


def preview(manifest: dict, repo: Path, revise: bool = False, groups: list[str] | None = None) -> int:
    """`groups` is the transient `<area>` work filter: it narrows which
    documents this run reports on and never touches `project.groups`."""
    scoped = set(groups or [])
    docs = [
        doc for doc in active_documents(manifest)
        if not scoped or doc.get("group") in scoped
    ]
    project = manifest.get("project", {})
    print(f"Generation plan — tier: {project.get('tier', 'unknown')}")
    profiles = project.get("profiles", {})
    for dimension in ("shapes", "platforms", "frameworks", "concerns", "audiences"):
        values = ", ".join(profiles.get(dimension, [])) or "none"
        print(f"  {dimension}: {values}")
    print()
    flow_index_path = repo / ".docforge" / "flow-index.json"
    entries = plan_entries(repo, manifest, flow_index_path, revise, groups=groups)
    manifest_entries = {entry["id"]: entry for entry in entries if not entry["is_flow"]}
    flow_entries = [entry for entry in entries if entry["is_flow"]]
    for doc in docs:
        entry = manifest_entries.get(doc["id"], {})
        action = entry.get("action", "?")
        reason = entry.get("reason", "")
        print(f"{doc['write_order']:03d}  {doc['id']:<28}  {doc['path']}")
        requires = ", ".join(doc.get("requires", [])) or "none"
        origins = ", ".join(
            f"{origin['kind']}:{origin['id']}"
            for origin in doc.get("selection", {}).get("origins", [])
        ) or "manifest"
        print(
            f"     {doc['group']} / {doc['type']} | depth: {doc['target_depth']} | "
            f"requires: {requires} | selected by: {origins} | action: {action} — {reason}"
        )
    if flow_entries:
        print()
        print("Flows:")
        for entry in flow_entries:
            label = f"{entry['flow_name']} ({entry['flow_id']})" if entry["flow_id"] else entry["path"]
            print(f"  {label} → {entry['path']}  [{entry['action']}] {entry['reason']}")
    flow_count = sum("flow_graph" in doc.get("requires", []) for doc in docs)
    summary = f"\n{len(docs)} manifest documents; {flow_count} require a flow graph"
    if flow_entries:
        summary += f"; {len(flow_entries)} main-priority flow documents"
    print(summary + ".")
    return 0


def title_for(doc: dict) -> str:
    return doc.get("title") or doc["id"].replace("-", " ").replace("_", " ").title()


def scaffold_entry(doc: dict, manifest: dict) -> dict:
    """Sidecar entry (public identity + provenance) for a fresh scaffold."""
    public = store.public_from_manifest(doc)
    provenance = build_provenance(
        doc["id"],
        doc["path"],
        tier=manifest.get("project", {}).get("tier", "<TIER>"),
        target_depth=doc["target_depth"],
    )
    entry = {key: value for key, value in public.items() if value}
    entry["provenance"] = provenance
    return entry


def table_header(block: str) -> tuple[list[str], int]:
    """Return the template's own header/separator lines and its column count.

    Both live between the markers, so a regenerated block that emits only data
    rows destroys them. Falls back to a two-column header when a template
    carries none, so the output is always a well-formed table."""
    lines = [line for line in block.splitlines() if line.strip()]
    for index in range(len(lines) - 1):
        head, rule = lines[index].strip(), lines[index + 1].strip()
        if head.startswith("|") and TABLE_SEPARATOR.match(rule):
            return [head, rule], rule.strip("|").count("|") + 1
    return ["| Document | Answers |", "|---|---|"], 2


def pad_row(cells: list[str], columns: int) -> str:
    """Render one row at the template's width; a narrower row breaks the table."""
    padded = cells[:columns] + ["—"] * max(0, columns - len(cells))
    return "| " + " | ".join(padded) + " |"


def child_rows(doc: dict, manifest: dict, columns: int = 2) -> list[str]:
    directory = PurePosixPath(doc["path"]).parent
    children = []
    for candidate in routable_children(doc, manifest):
        if candidate["id"] == doc["id"]:
            continue
        candidate_path = PurePosixPath(candidate["path"])
        try:
            relative = candidate_path.relative_to(directory)
        except ValueError:
            continue
        if len(relative.parts) == 1 or (len(relative.parts) == 2 and relative.name == "README.md"):
            children.append(candidate)
    children.sort(key=lambda item: (item["write_order"], item["path"]))
    rows = [
        pad_row(
            [
                f"[{title_for(child)}]({PurePosixPath(child['path']).relative_to(directory).as_posix()})",
                f"{{{{the reader question {child['id']} answers}}}}",
            ],
            columns,
        )
        for child in children
    ]
    if not rows:
        return [
            pad_row(
                [
                    "_No documents are selected in this section yet; they are written when repository evidence selects them._",
                    "—",
                ],
                columns,
            ),
        ]
    return rows


def expand_children_block(body: str, doc: dict, manifest: dict) -> str:
    start = body.find(CHILDREN_START)
    end = body.find(CHILDREN_END)
    if start == -1 or end == -1:
        return body
    header, columns = table_header(body[start + len(CHILDREN_START):end])
    rows = child_rows(doc, manifest, columns)
    block = CHILDREN_START + "\n" + "\n".join(header + rows) + "\n" + CHILDREN_END
    return body[:start] + block + body[end + len(CHILDREN_END):]


def scaffold_body(doc: dict, manifest: dict) -> str:
    if doc["type"] in INDEX_TYPES:
        template = SKILL_ROOT / doc["scaffold_template"]
        if not template.is_file():
            raise ValueError(f"template not found for {doc['id']}: {doc['scaffold_template']}")
        body = template.read_text(encoding="utf-8")
        state, _, body_start = codec_parse_frontmatter(body)
        if state != "missing":
            body = body[body_start:]
        body = expand_children_block(body, doc, manifest)
        return body.replace("{{TITLE}}", title_for(doc), 1)
    template = SKILL_ROOT / doc["scaffold_template"]
    if not template.is_file():
        raise ValueError(f"template not found for {doc['id']}: {doc['scaffold_template']}")
    body = template.read_text(encoding="utf-8")
    state, _, body_start = codec_parse_frontmatter(body)
    if state != "missing":
        body = body[body_start:]
    return body


def deep_merge(existing, defaults):
    if isinstance(existing, dict) and isinstance(defaults, dict):
        result = dict(existing)
        for key, value in defaults.items():
            result[key] = deep_merge(result[key], value) if key in result else value
        return result
    if isinstance(existing, list) and isinstance(defaults, list):
        return existing + [item for item in defaults if item not in existing]
    return existing


def ensure_local_ignore(repo: Path) -> None:
    ignore = repo / ".gitignore"
    text = ignore.read_text(encoding="utf-8") if ignore.exists() else ""
    lines = text.splitlines()
    if "CLAUDE.local.md" not in lines:
        suffix = "" if not text or text.endswith("\n") else "\n"
        ignore.write_text(text + suffix + "CLAUDE.local.md\n", encoding="utf-8")


def write_document(repo: Path, doc: dict, manifest: dict) -> str:
    target = repo / doc["path"]
    body = scaffold_body(doc, manifest)
    target.parent.mkdir(parents=True, exist_ok=True)
    if doc["type"] == "machine-config" and target.exists():
        existing = json.loads(target.read_text(encoding="utf-8"))
        defaults = json.loads(body)
        target.write_text(json.dumps(deep_merge(existing, defaults), indent=2) + "\n", encoding="utf-8")
        action = "merge"
    elif target.exists():
        action = "exists"
    else:
        target.write_text(body, encoding="utf-8")
        action = "create"
    if (
        action == "create"
        and doc.get("provenance_mode") == "sections"
        and doc["type"] != "machine-config"
        and doc["path"] not in MARKDOWN_EXCEPTIONS
    ):
        store.write_entry(repo, doc["path"], scaffold_entry(doc, manifest))
    if doc["path"] == "CLAUDE.local.md":
        ensure_local_ignore(repo)
    print(f"{action}  {doc['path']}")
    return action


def required_indexes(doc: dict, manifest: dict) -> list[dict]:
    doc_path = PurePosixPath(doc["path"])
    ancestors = []
    parent = doc_path.parent
    while str(parent) not in ("", "."):
        ancestors.append((parent / "README.md").as_posix())
        parent = parent.parent
    by_path = {item["path"]: item for item in active_documents(manifest)}
    indexes = [by_path[path] for path in reversed(ancestors) if path in by_path and path != doc["path"]]
    return indexes


def materialize(repo: Path, manifest: dict, doc_id: str) -> int:
    ensure_docforge_gitignore(repo / ".docforge")
    matches = [doc for doc in active_documents(manifest) if doc["id"] == doc_id]
    if not matches:
        return fail(f"document id not found or skipped: {doc_id}", 2)
    doc = matches[0]
    try:
        for index in required_indexes(doc, manifest):
            if not (repo / index["path"]).exists():
                write_document(repo, index, manifest)
        write_document(repo, doc, manifest)
    except (ValueError, json.JSONDecodeError) as exc:
        return fail(str(exc), 2)
    return 0


def heading_anchor(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^\w\s-]", "", value, flags=re.UNICODE)
    return re.sub(r"[\s-]+", "-", value).strip("-")


def provenance_defects(repo: Path, doc: dict, state: str, provenance: dict | None, body: str, tier: str | None = None) -> dict[str, list[str]]:
    result = {
        "missing provenance": [], "unparseable provenance": [],
        "legacy provenance": [], "obsolete schema": [], "empty provenance": [],
        "invalid blob": [], "unknown source": [], "unknown section": [],
    }
    if state == "missing":
        result["missing provenance"].append(doc["path"])
        return result
    if state == "unparseable":
        result["unparseable provenance"].append(doc["path"])
        return result
    if state == "obsolete":
        result["obsolete schema"].append(f"{doc['path']}: run migrate_metadata.py")
        return result
    if state == "legacy":
        result["legacy provenance"].append(doc["path"])
        return result
    if not isinstance(provenance, dict):
        result["missing provenance"].append(doc["path"])
        return result
    missing = sorted(PROVENANCE_FIELDS - set(provenance))
    graph = provenance.get("graph")
    if not isinstance(graph, dict) or not {"provider", "flow"} <= set(graph):
        missing.append("graph.provider/flow")
    generator = provenance.get("generator")
    if not isinstance(generator, dict) or not {"name", "version"} <= set(generator):
        missing.append("generator.name/version")
    if missing or provenance.get("schema") not in SUPPORTED_SCHEMA_VERSIONS or "graph_snapshot" in provenance:
        detail = ", ".join(missing) if missing else "invalid schema or obsolete graph_snapshot"
        result["missing provenance"].append(f"{doc['path']}: {detail}")
    sections = provenance.get("sections")
    if not isinstance(sections, list):
        result["missing provenance"].append(f"{doc['path']}: sections")
        return result
    if doc.get("status") in WRITTEN:
        concrete = [
            key for key in SCALAR_PROVENANCE_FIELDS
            if not isinstance(provenance.get(key), str)
            or not provenance[key]
            or SCAFFOLD_TOKEN.fullmatch(provenance[key])
        ]
        if isinstance(generator, dict):
            for key in ("name", "version"):
                value = generator.get(key)
                if not isinstance(value, str) or not value or SCAFFOLD_TOKEN.fullmatch(value):
                    concrete.append(f"generator.{key}")
        elif "generator" not in concrete:
            concrete.append("generator")
        if isinstance(graph, dict):
            concrete.extend(
                f"graph.{key}" for key in ("provider", "flow")
                if not isinstance(graph.get(key), str)
                or not graph[key]
                or SCAFFOLD_TOKEN.fullmatch(graph[key])
            )
        if concrete:
            result["missing provenance"].append(
                f"{doc['path']}: non-concrete {', '.join(sorted(concrete))}"
            )
        expected = {
            "doc_id": doc["id"],
            "path": doc["path"],
            "tier": tier,
            "target_depth": doc["target_depth"],
        }
        mismatched = [
            key for key, value in expected.items()
            if value is not None and provenance.get(key) != value
        ]
        if isinstance(graph, dict) and graph.get("flow") not in FLOW_VALUES:
            mismatched.append("graph.flow")
        git_commit = provenance.get("git_commit")
        if git_commit is not None and (
            not isinstance(git_commit, str) or not BLOB.fullmatch(git_commit)
        ):
            mismatched.append("git_commit")
        if mismatched:
            result["missing provenance"].append(
                f"{doc['path']}: invalid {', '.join(sorted(mismatched))}"
            )
        if not sections:
            result["empty provenance"].append(doc["path"])
    anchors = {
        heading_anchor(match.group(2))
        for line in body.splitlines()
        if (match := re.match(r"^(#{1,6})\s+(.+?)\s*#*\s*$", line))
    }
    for section in sections:
        section_id = section.get("id") if isinstance(section, dict) else None
        label = section_id if isinstance(section_id, str) else "<missing>"
        if not isinstance(section_id, str) or section_id not in anchors:
            result["unknown section"].append(f"{doc['path']}: {label}")
        for source in section.get("sources", []) if isinstance(section, dict) else []:
            source_path = source.get("path", "") if isinstance(source, dict) else ""
            blob = source.get("git_blob") if isinstance(source, dict) else None
            if not isinstance(blob, str) or not BLOB.fullmatch(blob):
                result["invalid blob"].append(f"{doc['path']}: {source_path or '<missing>'}")
            if not source_path or not (repo / source_path).is_file():
                result["unknown source"].append(f"{doc['path']}: {source_path or '<missing>'}")
            role = source.get("role") if isinstance(source, dict) else None
            if role not in SOURCE_ROLES:
                result["missing provenance"].append(f"{doc['path']}: invalid source role")
        if not isinstance(section, dict) or not isinstance(section.get("sources"), list) or not isinstance(section.get("unresolved"), list):
            result["missing provenance"].append(f"{doc['path']}: invalid section shape")
    return result


def coverage_scope(doc: dict) -> tuple[list[PurePosixPath], PurePosixPath]:
    """`(children_folders, link_base)` for a routing document.

    For an index the two coincide: `docs/reference/README.md` owns
    `docs/reference` and its links also resolve from there. For a merged
    compact file they diverge — `docs/reference.md` stands in for the index of
    `docs/reference`, so it owns that folder's children, but its own links
    resolve from `docs`. Using `.parent` for both is what silently exempted
    every merged file from this check.

    A merged file can stand in for more than one folder, and for folders its
    own path does not name: `docs/decisions.md` folds
    `docs/architecture/decisions/`, and `docs/operations.md` folds both
    `docs/operations/` and `docs/operations/runbooks/`. Take the folders from
    the members the file actually merged, not from its own path."""
    path = PurePosixPath(doc["path"])
    if doc["type"] != COMPACT_TYPE:
        return [path.parent], path.parent
    folders = {
        PurePosixPath(query_catalog.load_type(query_catalog.member_type_id(member))["path"]).parent
        for member in doc.get("compact_members", [])
    }
    folders.add(path.with_suffix(""))
    return sorted(folders), path.parent


def readme_child_coverage(repo: Path, doc: dict, manifest: dict, text: str) -> list[str]:
    """Every materialized direct child of a section index must be linked.

    Merged compact files carry the same duty. A group that spilled past the
    compact section cap keeps children at their own standard paths with no
    README above them — if the merged file does not link them, nothing does."""
    if doc["type"] not in INDEX_TYPES and doc["type"] != COMPACT_TYPE:
        return []
    children_folders, link_base = coverage_scope(doc)
    missing = []
    for candidate in routable_children(doc, manifest):
        if candidate["id"] == doc["id"]:
            continue
        candidate_path = PurePosixPath(candidate["path"])
        if not any(is_direct_child(folder, candidate_path) for folder in children_folders):
            continue
        if not (repo / candidate["path"]).is_file():
            continue
        try:
            rel = candidate_path.relative_to(link_base).as_posix()
        except ValueError:
            rel = candidate_path.as_posix()
        if rel not in text and f"./{rel}" not in text:
            missing.append(candidate["path"])
    return sorted(set(missing))


def is_direct_child(folder: PurePosixPath, candidate: PurePosixPath) -> bool:
    try:
        relative = candidate.relative_to(folder)
    except ValueError:
        return False
    return len(relative.parts) == 1 or (len(relative.parts) == 2 and relative.name == "README.md")


STRUCTURAL_GLYPHS = re.compile(r"[│├└┌┐┘┬┴┤─]")
# Accessibility directives and a closing `}` may precede the diagram
# declaration inside a mermaid fence.
MERMAID_DIRECTIVE = re.compile(r"^(?:accTitle|accDescr)\s*:|^\}$")


def illustration_forms(text: str) -> list[str]:
    """The form of every illustration in the document, in order.

    A Mermaid fence's form is the first token of its content, so a declared
    `sequenceDiagram` is no longer satisfied by whatever diagram happens to be
    present -- which is how a pre-baked ASCII layout tree passed for the one
    runtime scenario a 30 KB document owed."""
    forms: list[str] = []
    for fence in scan_fences(text):
        lines = [line.strip() for _, line in fence["lines"] if line.strip()]
        if fence["language"] == "mermaid":
            # `%%` comments and the `accTitle:` / `accDescr:` accessibility
            # directives may precede the declaration, so the kind is the first
            # line that is neither.
            body = [
                line for line in lines
                if not line.startswith("%%") and not MERMAID_DIRECTIVE.match(line)
            ]
            if body:
                forms.append(body[0].split()[0])
            continue
        if fence["language"] in {"text", "ascii", ""} and any(
            STRUCTURAL_GLYPHS.search(line) for line in lines
        ):
            forms.append("text")
    return forms


def has_declared_illustration(text: str) -> bool:
    """True when the file carries any recognized illustration."""
    return bool(illustration_forms(text))


def illustration_coverage(doc: dict, text: str) -> list[str]:
    """Every view a document declares must be present, by form.

    `illustration_views` lists the reader questions this type owes an answer
    to; a missing view is a question the document leaves unanswered. A view
    marked `required: false` is conditional on evidence (a data model that does
    not exist, a flow with one outcome) and is never demanded. Falls back to
    `dominant_form` for a type that declares no views."""
    if doc.get("group") == AGENT_CONTEXT_GROUP:
        return []
    if doc.get("path") in MARKDOWN_EXCEPTIONS or doc.get("type") == "machine-config":
        return []
    if doc.get("status") not in WRITTEN:
        return []
    present = illustration_forms(text)
    views = [
        view for view in doc.get("illustration_views") or []
        if view.get("required", True)
    ]
    if views:
        findings = []
        remaining = list(present)
        for view in views:
            form = view.get("form")
            if form in remaining:
                remaining.remove(form)
                continue
            findings.append(
                f"{doc['path']}: missing the {form} view in \"{view.get('section')}\" "
                f"({view.get('question')})"
            )
        return findings
    form = doc.get("dominant_form")
    if form is None or form == "table":
        return []
    if present:
        return []
    return [f"{doc['path']}: declared dominant_form {form}, no mermaid or structural text fence"]


def cohesion_defects(docs: list[dict], texts: dict[str, str]) -> list[str]:
    """No document is an island: in a section folder holding two or more
    written non-router documents, each either links a sibling or is linked by
    one. The section README alone does not satisfy it."""
    findings: list[str] = []
    by_folder: dict[str, list[dict]] = {}
    for doc in docs:
        if doc.get("group") == AGENT_CONTEXT_GROUP:
            continue
        if doc["type"] in INDEX_TYPES or doc["type"] == COMPACT_TYPE:
            continue
        if doc.get("status") not in WRITTEN:
            continue
        by_folder.setdefault(str(PurePosixPath(doc["path"]).parent), []).append(doc)
    for folder, members in sorted(by_folder.items()):
        if len(members) < 2:
            continue
        sibling_paths = {member["path"] for member in members}
        outgoing: dict[str, set[str]] = {}
        for member in members:
            member_path = member["path"]
            base = PurePosixPath(member_path).parent
            linked = set()
            for raw in LINK.findall(texts.get(member_path, "")):
                target = raw.split("#", 1)[0].strip()
                if not target or target.startswith(("http://", "https://", "mailto:")):
                    continue
                if PLACEHOLDER.search(target) or TOKEN.search(target):
                    continue
                normalized = posixpath.normpath(str(base / target))
                if normalized in sibling_paths and normalized != member_path:
                    linked.add(normalized)
            outgoing[member_path] = linked
        linked_by = {target for linked in outgoing.values() for target in linked}
        for member in members:
            member_path = member["path"]
            if not outgoing.get(member_path) and member_path not in linked_by:
                findings.append(f"{folder}: {member_path} is an island — links no sibling and no sibling links it")
    return findings


def audit(repo: Path, manifest: dict) -> int:
    identity = identity_of(manifest)
    web_base = identity["web_base"] if identity else None
    findings: dict[str, list[str]] = {
        "missing": [],
        "unfilled scaffold": [],
        "missing provenance": [],
        "unparseable provenance": [],
        "legacy provenance": [],
        "obsolete schema": [],
        "empty provenance": [],
        "invalid blob": [],
        "unknown source": [],
        "unknown section": [],
        "broken links": [],
        "readme child coverage": [],
        "illustration coverage": [],
        "section cohesion": [],
        "agent-context leak": [],
        "agent-context outbound": [],
        "invalid json": [],
        "folder-only promotion": [],
        "forge leakage": [],
        "unexpected": [],
    }
    tokens: list[str] = []
    texts: dict[str, str] = {}
    docs = active_documents(manifest)
    expected = {doc["path"] for doc in docs}
    self_managed = unmanaged_paths(manifest)
    for root_name in ("docs", "docs-portfolio"):
        root = repo / root_name
        if root.is_dir():
            for existing in root.rglob("*.md"):
                rel = existing.relative_to(repo).as_posix()
                if "_archive" not in existing.parts and rel not in expected and rel not in self_managed:
                    findings["unexpected"].append(rel)
    for doc in docs:
        target = repo / doc["path"]
        if not target.is_file():
            findings["missing"].append(doc["path"])
            continue
        text = target.read_text(encoding="utf-8", errors="replace")
        findings["agent-context leak"].extend(
            f"{doc['path']}:{finding['line']} [{finding['kind']}] -> {finding['target']}"
            for finding in agent_context_leaks(doc, manifest, text)
        )
        findings["agent-context outbound"].extend(
            f"{doc['path']}:{finding['line']} [{finding['kind']}] -> {finding['target']}"
            for finding in agent_context_outbound_findings(doc, manifest, text)
        )
        if doc["type"] == "machine-config":
            try:
                json.loads(text)
            except json.JSONDecodeError:
                findings["invalid json"].append(doc["path"])
            continue
        placeholders = PLACEHOLDER.findall(text)
        if placeholders:
            findings["unfilled scaffold"].append(f"{doc['path']} ({len(placeholders)})")
        found_tokens = sorted(set(TOKEN.findall(text)))
        if found_tokens:
            tokens.append(f"{doc['path']}: {', '.join(found_tokens)}")
        # A declared permalink base is the one sanctioned place a forge name may
        # appear; without this every GitHub- or GitLab-hosted repository would
        # trip on every source link it is now expected to carry.
        scrubbed = text.replace(web_base, "") if web_base else text
        forge_hits = sorted({match.group(0).lower() for match in FORGE.finditer(scrubbed)})
        if forge_hits:
            findings["forge leakage"].append(f"{doc['path']}: {', '.join(forge_hits)}")
        if doc["provenance_mode"] == "sections" and doc["path"] not in MARKDOWN_EXCEPTIONS:
            meta = store.read_doc_metadata(repo, doc)
            # An un-migrated inline document is a legacy finding, not a pass.
            state = "legacy" if meta["state"] == "inline" else meta["state"]
            provenance = meta["provenance"]
            body = text
            for kind, items in provenance_defects(
                repo, doc, state, provenance, body, manifest.get("project", {}).get("tier")
            ).items():
                findings[kind].extend(items)
        for link in LINK.findall(text):
            clean = link.split("#", 1)[0]
            if not clean or clean.startswith(("http://", "https://", "mailto:")):
                continue
            if PLACEHOLDER.search(clean) or TOKEN.search(clean):
                continue
            if not (target.parent / clean).resolve().exists():
                findings["broken links"].append(f"{doc['path']} -> {link}")
        findings["readme child coverage"].extend(
            f"{doc['path']}: missing link to {item}"
            for item in readme_child_coverage(repo, doc, manifest, text)
        )
        findings["illustration coverage"].extend(illustration_coverage(doc, text))
        texts[doc["path"]] = text
    findings["section cohesion"].extend(cohesion_defects(docs, texts))
    for prefix, root_counts in COLLECTION_PREFIXES.items():
        root = prefix.rstrip("/")
        folders = {
            str(PurePosixPath(path).parent)
            for path in expected
            if path.startswith(prefix)
        }
        if root_counts:
            folders.add(root)
        else:
            folders.discard(root)
        for folder in sorted(folders):
            if f"{folder}/README.md" in expected:
                children = [
                    path for path in expected
                    if str(PurePosixPath(path).parent) == folder and not path.endswith("/README.md")
                ]
                if not children:
                    findings["folder-only promotion"].append(folder)
    total = sum(len(items) for items in findings.values())
    for label, items in findings.items():
        items.sort()
        if items:
            print(f"{label.upper()} ({len(items)})")
            for item in items:
                print(f"  {item}")
            print()
    if tokens:
        print(f"EXTERNAL TOKENS ({len(tokens)})")
        for item in tokens:
            print(f"  {item}")
        print()
    print(f"{len(docs)} manifest documents checked, {total} defects.")
    return 1 if total else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--dry-run", action="store_true")
    modes.add_argument("--document")
    modes.add_argument("--audit", action="store_true")
    parser.add_argument("--revise", action="store_true")
    parser.add_argument(
        "--group", action="append", default=[],
        help="Narrow --dry-run to these catalog groups (the transient <area> "
             "work filter; never changes project.groups)",
    )
    args = parser.parse_args()
    if not args.repo.is_dir():
        return fail(f"not a directory: {args.repo}", 2)
    try:
        manifest = load_manifest(
            resolve_manifest(args.manifest, args.repo),
            require_documents=True,
        )
    except (ValueError, json.JSONDecodeError) as exc:
        return fail(str(exc), 2)
    if args.dry_run:
        try:
            scoped_groups = query_catalog.normalize_groups(args.group)
        except ValueError as exc:
            return fail(str(exc), 2)
        return preview(manifest, args.repo, args.revise, groups=scoped_groups)
    if args.document:
        return materialize(args.repo, manifest, args.document)
    return audit(args.repo, manifest)


if __name__ == "__main__":
    raise SystemExit(main())
