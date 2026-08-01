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


def docforge_status(repo_path: Path) -> str:
    arch = repo_path / "docs" / "architecture"
    has_overview = (arch / "high-level.md").exists() or (arch / "overview.md").exists()
    has_manifest = (repo_path / ".docforge" / "manifest.json").exists()
    if has_manifest:
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

    collection = [{
        "path": str(root),
        "membership": "parent",
        "status": docforge_status(root),
    }]

    for rel_path, meta in declared.items():
        full = root / rel_path
        collection.append({
            "path": str(full),
            "membership": "declared (submodule)",
            "submodule_name": meta.get("name"),
            "submodule_url": meta.get("url"),
            "status": docforge_status(full) if full.exists() else "not checked out locally",
        })

    for full in detected:
        collection.append({
            "path": str(full),
            "membership": "detected — NOT in .gitmodules",
            "status": docforge_status(full),
        })

    needs_generation = [c for c in collection if c["status"].startswith("none")]
    dependency_edges = resolve_dependency_edges(root, collection)

    if args.json:
        print(json.dumps({
            "root": str(root),
            "collection": collection,
            "needs_generation": [c["path"] for c in needs_generation],
            "dependency_edges": dependency_edges,
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


if __name__ == "__main__":
    main()
