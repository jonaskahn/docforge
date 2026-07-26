#!/usr/bin/env python3
"""
discover_repos.py — assemble the full repo collection for a docforge
diligence job: the parent, every declared git submodule, and every nested
repo detected on disk that ISN'T declared in .gitmodules (vendored copies,
git-subtree merges, manually cloned submodules).

For each repo found, reports whether it already has a docforge baseline
(docs/architecture/overview.md) and/or a docforge provenance manifest
(.docforge/manifest.json), so the caller knows which repos need
generation before a diligence portfolio layer is built on top of them.

Usage:
    python discover_repos.py --root <parent-repo-path>
    python discover_repos.py --root <parent-repo-path> --json
    python discover_repos.py --root <parent-repo-path> --exclude node_modules --exclude vendor/cache
"""

import argparse
import configparser
import json
import subprocess
from pathlib import Path

DEFAULT_EXCLUDES = {".git", "node_modules", ".venv", "venv", "__pycache__", "dist", "build"}


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
    has_overview = (repo_path / "docs" / "architecture" / "overview.md").exists()
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

    if args.json:
        print(json.dumps({
            "root": str(root),
            "collection": collection,
            "needs_generation": [c["path"] for c in needs_generation],
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


if __name__ == "__main__":
    main()
