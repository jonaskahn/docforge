#!/usr/bin/env python3
"""
discover_child_repos.py — assemble the full repo collection for a docforge
diligence job: the parent, every declared git submodule, and every nested
repo detected on disk that ISN'T declared in .gitmodules (vendored copies,
git-subtree merges, manually cloned submodules).

For each repo found, reports whether it already has a docforge baseline
(docs/architecture/high-level.md) and/or a docforge provenance manifest
(.docforge/manifest.json), so the caller knows which repos need
generation before a diligence portfolio layer is built on top of them.

Usage:
    python discover_child_repos.py --root <parent-repo-path>
    python discover_child_repos.py --root <parent-repo-path> --json
    python discover_child_repos.py --root <parent-repo-path> --exclude node_modules --exclude vendor/cache
"""

import argparse
import configparser
import json
import subprocess
from pathlib import Path

from runtime.common.python import manifest_deps

DEFAULT_EXCLUDES = {".git", "node_modules", ".venv", "venv", "__pycache__", "dist", "build"}
IGNORED_WALK = DEFAULT_EXCLUDES | {
    ".codegraph", ".gitnexus", ".docforge", ".build", "DerivedData",
}


def parse_gitmodules(root: Path) -> dict:
    """Returns {relative_path: {'name': ..., 'url': ...}} for declared submodules."""
    gm_path = root / ".gitmodules"
    if not gm_path.exists():
        return {}
    parser = configparser.ConfigParser()
    try:
        parser.read(gm_path)
    except configparser.Error:
        return {}
    declared = {}
    for section in parser.sections():
        if not section.startswith("submodule"):
            continue
        name = section.split('"')[1] if '"' in section else section
        path = parser.get(section, "path", fallback=None)
        url = parser.get(section, "url", fallback=None)
        if path:
            declared[str(Path(path).as_posix())] = {"name": name, "url": url}
    return declared


def has_own_git(path: Path) -> bool:
    """True if `path` is itself a git repo (a .git dir, or a .git file
    pointing elsewhere — the shape submodule worktrees and some worktree
    checkouts use)."""
    git_marker = path / ".git"
    return git_marker.is_dir() or git_marker.is_file()


def find_nested_repos(root: Path, excludes: set) -> list:
    """Walk the tree under root (excluding root itself) for any directory
    that is its own git repo."""
    found = []
    for dirpath in root.rglob("*"):
        if not dirpath.is_dir():
            continue
        if dirpath == root:
            continue
        if any(part in excludes for part in dirpath.relative_to(root).parts):
            continue
        if has_own_git(dirpath):
            found.append(dirpath)
    return found


def read_manifest_tier(repo_path: Path) -> str | None:
    """Best-effort read of project.tier from .docforge/manifest.json."""
    path = repo_path / ".docforge" / "manifest.json"
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data.get("project", {}).get("tier")


def docforge_status(repo_path: Path, tier: str | None = None) -> str:
    arch = repo_path / "docs" / "architecture"
    has_overview = (arch / "high-level.md").exists() or (arch / "overview.md").exists()
    has_manifest = (repo_path / ".docforge" / "manifest.json").exists()
    if has_manifest:
        if tier:
            return f"docforge baseline + provenance (tier: {tier})"
        return "docforge baseline + provenance"
    if has_overview:
        return "docforge baseline present (no provenance manifest yet)"
    return "none — needs generation"


def git_submodule_status(root: Path) -> str:
    """Best-effort extra signal from git itself; purely informational."""
    try:
        out = subprocess.run(
            ["git", "submodule", "status", "--recursive"],
            cwd=root, capture_output=True, text=True, check=True,
        )
        return out.stdout.strip()
    except Exception:
        return ""


def inventory_manifests(repo: Path) -> list[tuple[str, Path]]:
    found: list[tuple[str, Path]] = []

    def walk(directory: Path) -> None:
        for path in sorted(directory.iterdir(), key=lambda item: item.name):
            if path.name in IGNORED_WALK or path.is_symlink():
                continue
            if path.is_dir():
                walk(path)
            elif path.is_file():
                found.append((path.relative_to(repo).as_posix(), path))

    if repo.is_dir():
        walk(repo)
    return found


def load_repo_identity(root: Path) -> dict[tuple[str, str], dict]:
    """Map (ecosystem, name) → identity row from optional repo-identity.json."""
    path = root / ".metadata" / "portfolio" / "repo-identity.json"
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    mapping: dict[tuple[str, str], dict] = {}
    for row in data.get("packages", []):
        ecosystem = row.get("ecosystem")
        name = row.get("name")
        if not ecosystem or not name:
            continue
        key = (ecosystem, manifest_deps.normalize(ecosystem, name))
        mapping[key] = row
    return mapping


def resolve_dependency_edges(root: Path, members: list[dict]) -> list[dict]:
    """Resolve directed edges between members via mapping file, then heuristic."""
    identity_map = load_repo_identity(root)
    member_dirs = []
    for item in members:
        path = Path(item["path"])
        if path.is_dir() and item.get("membership") != "parent":
            member_dirs.append((item, path))
    if len(member_dirs) < 2 and not identity_map:
        # Still allow parent↔member when identities exist; otherwise need 2+ members.
        pass

    # Per-member: own package ids and declared dependencies.
    per_member: list[dict] = []
    identity_owners: dict[tuple[str, str], str] = {}
    for item, path in member_dirs:
        files = inventory_manifests(path)
        identities = manifest_deps.extract_package_identities(files)
        dependencies = manifest_deps.extract_dependencies(files)
        repo_id = path.name
        for ecosystem, names in identities.items():
            for name in names:
                identity_owners.setdefault((ecosystem, name), repo_id)
        per_member.append({
            "repo_id": repo_id,
            "path": str(path),
            "identities": identities,
            "dependencies": dependencies,
        })

    # Mapping file overrides / supplements identity → repo_id.
    for (ecosystem, name), row in identity_map.items():
        identity_owners[(ecosystem, name)] = row["repo_id"]

    edges: list[dict] = []
    seen: set[tuple[str, str, str]] = set()
    for member in per_member:
        for ecosystem, deps in member["dependencies"].items():
            for dep_name in deps:
                key = (ecosystem, dep_name)
                target = identity_owners.get(key)
                if target is None or target == member["repo_id"]:
                    continue
                resolution = "mapping" if key in identity_map else "heuristic"
                coupling = "shared library"
                if key in identity_map and identity_map[key].get("coupling_default"):
                    coupling = identity_map[key]["coupling_default"]
                edge_key = (member["repo_id"], target, coupling)
                if edge_key in seen:
                    continue
                seen.add(edge_key)
                edges.append({
                    "repo": member["repo_id"],
                    "depends_on": target,
                    "coupling_type": coupling,
                    "resolution": resolution,
                    "ecosystem": ecosystem,
                    "package": dep_name,
                })
    edges.sort(key=lambda row: (row["repo"], row["depends_on"], row["package"]))
    return edges


def load_flow_signatures(repo_path: Path) -> list[dict]:
    """A member's own exposed flow entry points, read from its own already
    materialized .docforge/flow-index.json — never a fresh graph query."""
    path = repo_path / ".docforge" / "flow-index.json"
    if not path.is_file():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    signatures = []
    for flow in data.get("flows", []):
        entry_ref = flow.get("entry_ref") or {}
        kind = entry_ref.get("kind")
        signature = entry_ref.get("signature")
        if kind and signature:
            signatures.append({"kind": kind, "signature": signature})
    return signatures


def load_flow_evidence_text(repo_path: Path) -> str:
    """Searchable text of a member's own flow evidence, for heuristic
    boundary matching against a sibling's exposed entry-point signature."""
    path = repo_path / ".docforge" / "flow-index.json"
    if not path.is_file():
        return ""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return ""
    return json.dumps(data.get("flows", []))


def load_repo_identity_flows(root: Path) -> list[dict]:
    """Directed (repo -> counterpart) rows from the optional `flows` array in
    repo-identity.json; a `consumer`-role row is normalized to the same
    caller -> callee direction as a `producer`-role row."""
    path = root / ".metadata" / "portfolio" / "repo-identity.json"
    if not path.is_file():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    edges = []
    for row in data.get("flows", []):
        repo_id = row.get("repo_id")
        counterpart = row.get("counterpart_repo_id")
        channel = row.get("channel") or {}
        signature = channel.get("signature")
        if not (repo_id and counterpart and signature):
            continue
        if row.get("role") == "consumer":
            repo_id, counterpart = counterpart, repo_id
        edges.append({"repo": repo_id, "counterpart": counterpart, "channel": channel})
    return edges


def resolve_flow_edges(root: Path, members: list[dict]) -> list[dict]:
    """Resolve directed cross-repo flow-boundary edges: an explicit mapping
    row first, then a heuristic signature match against each member's own
    flow-index.json. Never invents an edge without one of these two signals,
    and never queries a graph across repo boundaries — flow-index.json is
    already materialized by that member's own Diligence run."""
    member_dirs = [
        Path(item["path"])
        for item in members
        if item.get("membership") != "parent" and Path(item["path"]).is_dir()
    ]

    signatures_by_repo: dict[str, list[dict]] = {}
    evidence_by_repo: dict[str, str] = {}
    for path in member_dirs:
        repo_id = path.name
        signatures_by_repo[repo_id] = load_flow_signatures(path)
        evidence_by_repo[repo_id] = load_flow_evidence_text(path)

    edges: list[dict] = []
    seen: set[tuple[str, str, str]] = set()

    for row in load_repo_identity_flows(root):
        repo_id = row["repo"]
        counterpart = row["counterpart"]
        channel = row["channel"]
        signature = channel.get("signature")
        key = (repo_id, counterpart, signature)
        if key in seen:
            continue
        seen.add(key)
        edges.append({
            "repo": repo_id,
            "counterpart": counterpart,
            "channel_kind": channel.get("kind"),
            "signature": signature,
            "resolution": "mapping",
        })

    for owner_id, signatures in signatures_by_repo.items():
        for sig in signatures:
            signature = sig["signature"]
            for caller_id, evidence_text in evidence_by_repo.items():
                if caller_id == owner_id:
                    continue
                if signature and signature in evidence_text:
                    key = (caller_id, owner_id, signature)
                    if key in seen:
                        continue
                    seen.add(key)
                    edges.append({
                        "repo": caller_id,
                        "counterpart": owner_id,
                        "channel_kind": sig["kind"],
                        "signature": signature,
                        "resolution": "heuristic",
                    })

    edges.sort(key=lambda row: (row["repo"], row["counterpart"], row["signature"]))
    return edges


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, required=True)
    ap.add_argument("--exclude", action="append", default=[],
                     help="Additional directory name to skip while walking (repeatable)")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    root = args.root.resolve()
    excludes = DEFAULT_EXCLUDES | set(args.exclude)

    declared = parse_gitmodules(root)
    nested = find_nested_repos(root, excludes)

    declared_paths = {root / p for p in declared}
    detected = [p for p in nested if p not in declared_paths]

    root_tier = read_manifest_tier(root)
    collection = [{
        "path": str(root),
        "membership": "parent",
        "status": docforge_status(root, root_tier),
        "tier": root_tier,
    }]

    for rel_path, meta in declared.items():
        full = root / rel_path
        if full.exists():
            tier = read_manifest_tier(full)
            status = docforge_status(full, tier)
        else:
            tier = None
            status = "not checked out locally"
        collection.append({
            "path": str(full),
            "membership": "declared (submodule)",
            "submodule_name": meta.get("name"),
            "submodule_url": meta.get("url"),
            "status": status,
            "tier": tier,
        })

    for full in detected:
        tier = read_manifest_tier(full)
        collection.append({
            "path": str(full),
            "membership": "detected — NOT in .gitmodules",
            "status": docforge_status(full, tier),
            "tier": tier,
        })

    needs_generation = [c for c in collection if c["status"].startswith("none")]
    dependency_edges = resolve_dependency_edges(root, collection)
    flow_edges = resolve_flow_edges(root, collection)

    if args.json:
        print(json.dumps({
            "root": str(root),
            "collection": collection,
            "needs_generation": [c["path"] for c in needs_generation],
            "dependency_edges": dependency_edges,
            "flow_edges": flow_edges,
        }, indent=2))
        return

    print(f"Repo collection under {root}\n")
    for c in collection:
        flag = "  <-- needs docforge generation before diligence" if c["status"].startswith("none") else ""
        print(f"[{c['membership']}] {c['path']}\n    status: {c['status']}{flag}\n")

    if any(c["membership"].startswith("detected") for c in collection):
        print("NOTE: one or more detected child repos are not declared in .gitmodules.")
        print("      Confirm with the repo owner whether each is in scope before proceeding.\n")

    if needs_generation:
        print(f"{len(needs_generation)} repo(s) need a docforge baseline before the portfolio layer is built:")
        for c in needs_generation:
            print(f"  - {c['path']}")

    if dependency_edges:
        print(f"\n{len(dependency_edges)} dependency edge(s):")
        for edge in dependency_edges:
            print(
                f"  - {edge['repo']} → {edge['depends_on']} "
                f"({edge['coupling_type']}, {edge['resolution']})"
            )

    if flow_edges:
        print(f"\n{len(flow_edges)} flow edge(s):")
        for edge in flow_edges:
            print(
                f"  - {edge['repo']} → {edge['counterpart']} "
                f"({edge['channel_kind']}: {edge['signature']}, {edge['resolution']})"
            )


if __name__ == "__main__":
    main()
