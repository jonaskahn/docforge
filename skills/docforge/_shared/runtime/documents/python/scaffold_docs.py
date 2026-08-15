#!/usr/bin/env python3
"""Preview, materialize, or audit the exact tree in a Docforge manifest."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path, PurePosixPath

from runtime.common.python._util import ensure_docforge_gitignore, fail, load_manifest, unmanaged_paths
from runtime.common.python.plan import plan_entries
from runtime.common.python.special_files import SPECIAL_DOC_OUTPUTS
from runtime.common.python.provenance_frontmatter import (
    BLOB,
    FLOW_VALUES,
    PROVENANCE_FIELDS,
    SCAFFOLD_TOKEN,
    SOURCE_ROLES,
    SUPPORTED_SCHEMA_VERSIONS,
    emit_document_frontmatter,
    parse_frontmatter as codec_parse_frontmatter,
    scaffold_provenance as build_provenance,
)
from runtime.common.python import provenance_store as store

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
CHILDREN_START = "<!-- docforge-children:start -->"
CHILDREN_END = "<!-- docforge-children:end -->"


def resolve_manifest(value: Path, repo: Path) -> Path:
    if value.is_absolute():
        return value
    direct = value.resolve()
    repo_relative = (repo / value).resolve()
    return direct if direct.exists() else repo_relative


def active_documents(manifest: dict) -> list[dict]:
    return [doc for doc in manifest["documents"] if doc.get("status") not in {"skipped", "retired"}]


def preview(manifest: dict, repo: Path, revise: bool = False) -> int:
    docs = active_documents(manifest)
    project = manifest.get("project", {})
    print(f"Generation plan — tier: {project.get('tier', 'unknown')}")
    profiles = project.get("profiles", {})
    for dimension in ("shapes", "platforms", "frameworks", "concerns", "audiences"):
        values = ", ".join(profiles.get(dimension, [])) or "none"
        print(f"  {dimension}: {values}")
    print()
    flow_index_path = repo / ".docforge" / "flow-index.json"
    entries = plan_entries(repo, manifest, flow_index_path, revise)
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


def scaffold_provenance(doc: dict, manifest: dict) -> str:
    provenance = build_provenance(
        doc["id"],
        doc["path"],
        tier=manifest.get("project", {}).get("tier", "<TIER>"),
        target_depth=doc["target_depth"],
    )
    return emit_document_frontmatter(doc["id"], title_for(doc), provenance)


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


def child_rows(doc: dict, manifest: dict) -> list[str]:
    directory = PurePosixPath(doc["path"]).parent
    children = []
    for candidate in active_documents(manifest):
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
        f"| [{title_for(child)}]({PurePosixPath(child['path']).relative_to(directory).as_posix()}) | {{{{the reader question {child['id']} answers}}}} |"
        for child in children
    ]
    if not rows:
        return [
            "| _No documents are selected in this section yet; they are written when repository evidence selects them._ | — |",
        ]
    return rows


def expand_children_block(body: str, doc: dict, manifest: dict) -> str:
    start = body.find(CHILDREN_START)
    end = body.find(CHILDREN_END)
    if start == -1 or end == -1:
        return body
    rows = child_rows(doc, manifest)
    block = CHILDREN_START + "\n" + "\n".join(rows) + "\n" + CHILDREN_END
    return body[:start] + block + body[end + len(CHILDREN_END):]


def scaffold_body(doc: dict, manifest: dict, storage: str) -> str:
    if doc["type"] in INDEX_TYPES:
        template = SKILL_ROOT / doc["scaffold_template"]
        if not template.is_file():
            raise ValueError(f"template not found for {doc['id']}: {doc['scaffold_template']}")
        body = template.read_text(encoding="utf-8")
        state, _, body_start = codec_parse_frontmatter(body)
        if state != "missing":
            body = body[body_start:]
        if storage == store.STORAGE_MARKDOWN and doc["path"] not in MARKDOWN_EXCEPTIONS:
            body = scaffold_provenance(doc, manifest) + body
        body = expand_children_block(body, doc, manifest)
        return body.replace("{{TITLE}}", title_for(doc), 1)
    template = SKILL_ROOT / doc["scaffold_template"]
    if not template.is_file():
        raise ValueError(f"template not found for {doc['id']}: {doc['scaffold_template']}")
    body = template.read_text(encoding="utf-8")
    state, _, body_start = codec_parse_frontmatter(body)
    if state != "missing":
        body = body[body_start:]
    if storage == store.STORAGE_MARKDOWN and doc["path"] not in MARKDOWN_EXCEPTIONS:
        body = scaffold_provenance(doc, manifest) + body
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
    storage = store.storage_for(manifest)
    target = repo / doc["path"]
    body = scaffold_body(doc, manifest, storage)
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
        and storage == store.STORAGE_JSON
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


def readme_child_coverage(repo: Path, doc: dict, manifest: dict, text: str) -> list[str]:
    """Every materialized direct child of a section README must be linked."""
    if doc["type"] not in INDEX_TYPES:
        return []
    directory = PurePosixPath(doc["path"]).parent
    missing = []
    for candidate in active_documents(manifest):
        if candidate["id"] == doc["id"]:
            continue
        try:
            relative = PurePosixPath(candidate["path"]).relative_to(directory)
        except ValueError:
            continue
        if not (len(relative.parts) == 1 or (len(relative.parts) == 2 and relative.name == "README.md")):
            continue
        if not (repo / candidate["path"]).is_file():
            continue
        rel = relative.as_posix()
        if rel not in text and f"./{rel}" not in text:
            missing.append(candidate["path"])
    return missing


def audit(repo: Path, manifest: dict) -> int:
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
        "invalid json": [],
        "folder-only promotion": [],
        "forge leakage": [],
        "unexpected": [],
    }
    tokens: list[str] = []
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
        forge_hits = sorted({match.group(0).lower() for match in FORGE.finditer(text)})
        if forge_hits:
            findings["forge leakage"].append(f"{doc['path']}: {', '.join(forge_hits)}")
        if doc["provenance_mode"] == "sections" and doc["path"] not in MARKDOWN_EXCEPTIONS:
            storage = store.storage_for(manifest)
            if storage == store.STORAGE_JSON:
                meta = store.read_doc_metadata(repo, doc, storage)
                state = "legacy" if meta["state"] == "inline" else meta["state"]
                provenance = meta["provenance"]
                body = text
            else:
                state, provenance, body_start = codec_parse_frontmatter(text)
                body = text[body_start:]
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
    for prefix in ("docs/flows/", "docs/architecture/concepts/"):
        folders = {
            str(PurePosixPath(path).parent)
            for path in expected
            if path.startswith(prefix) and len(PurePosixPath(path).parts) > len(PurePosixPath(prefix).parts)
        }
        for folder in sorted(folders):
            if folder == prefix.rstrip("/"):
                continue
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
        return preview(manifest, args.repo, args.revise)
    if args.document:
        return materialize(args.repo, manifest, args.document)
    return audit(args.repo, manifest)


if __name__ == "__main__":
    raise SystemExit(main())
