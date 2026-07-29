#!/usr/bin/env python3
"""Detect Docforge shape, platform, framework, and concern profile candidates."""

from __future__ import annotations

import argparse
import fnmatch
import json
import sys
from pathlib import Path, PurePosixPath

import manifest_deps

SKILL_ROOT = Path(__file__).resolve().parent.parent
CATALOG_PATH = SKILL_ROOT / ".metadata" / "catalog.json"
DIMENSIONS = ["shapes", "platforms", "frameworks", "concerns"]
IGNORED = {
    ".git", ".codegraph", ".gitnexus", ".docforge", "node_modules",
    ".build", "build", "dist", "DerivedData", ".venv", "venv", "__pycache__",
}
MAX_FILES = 25000
MAX_CONTENT_BYTES = 1024 * 1024
MAX_TOTAL_CONTENT_BYTES = 32 * 1024 * 1024
MAX_EVIDENCE = 20
TEXT_SUFFIXES = {
    ".c", ".cc", ".cpp", ".cs", ".dart", ".go", ".gradle", ".h", ".hpp",
    ".csproj", ".html", ".java", ".js", ".json", ".jsx", ".kt", ".kts", ".m",
    ".md", ".mm", ".pbxproj", ".php", ".plist", ".properties", ".py", ".rb", ".rs", ".sh",
    ".sol", ".swift", ".toml", ".ts", ".tsx", ".txt", ".xml", ".yaml", ".yml",
}
TEXT_NAMES = {
    "CMakeLists.txt", "Dockerfile", "Gemfile", "Makefile", "Podfile",
    "requirements.txt",
}


def matches_path(relative: str, pattern: str) -> bool:
    path = PurePosixPath(relative)
    patterns = [pattern]
    if pattern.startswith("**/"):
        patterns.append(pattern[3:])
    return any(
        fnmatch.fnmatchcase(relative, candidate) or path.match(candidate)
        for candidate in patterns
    )


def inventory(repo: Path) -> list[tuple[str, Path]]:
    found: list[tuple[str, Path]] = []

    def walk(directory: Path) -> None:
        if len(found) >= MAX_FILES:
            return
        for path in sorted(directory.iterdir(), key=lambda item: item.name):
            if path.name in IGNORED or path.is_symlink():
                continue
            if path.is_dir():
                walk(path)
            elif path.is_file():
                found.append((path.relative_to(repo).as_posix(), path))
            if len(found) >= MAX_FILES:
                return

    walk(repo)
    return found


def detect(repo: Path) -> list[dict]:
    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    files = inventory(repo)
    dependencies = manifest_deps.extract_dependencies(files)
    cache: dict[Path, str] = {}
    cached_bytes = 0
    results: list[dict] = []
    for dimension in DIMENSIONS:
        for profile in catalog["profiles"][dimension]:
            evidence: list[str] = []
            matched_kinds: set[str] = set()
            for signal in profile.get("signals", []):
                if signal["kind"] == "dependency":
                    ecosystem = signal.get("ecosystem", "")
                    key = manifest_deps.normalize(ecosystem, signal.get("name", ""))
                    for manifest_path in dependencies.get(ecosystem, {}).get(key, []):
                        evidence.append(manifest_path)
                        matched_kinds.add("dependency")
                    continue
                for relative, path in files:
                    if not matches_path(relative, signal["pattern"]):
                        continue
                    if signal["kind"] == "content":
                        size = path.stat().st_size
                        if (
                            path.suffix.lower() not in TEXT_SUFFIXES
                            and path.name not in TEXT_NAMES
                        ):
                            continue
                        if size > MAX_CONTENT_BYTES:
                            continue
                        if path not in cache:
                            if cached_bytes + size > MAX_TOTAL_CONTENT_BYTES:
                                continue
                            cache[path] = path.read_text(encoding="utf-8", errors="replace")
                            cached_bytes += size
                        if signal.get("contains", "") not in cache[path]:
                            continue
                    evidence.append(relative)
                    matched_kinds.add(signal["kind"])
            evidence = sorted(set(evidence))
            if not evidence:
                continue
            confidence = (
                "confirmed"
                if matched_kinds & {"path", "dependency"} or len(evidence) >= 2
                else "candidate"
            )
            results.append({
                "dimension": dimension,
                "id": profile["id"],
                "confidence": confidence,
                "evidence": evidence[:MAX_EVIDENCE],
            })
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    if not args.repo.is_dir():
        print(f"error: not a directory: {args.repo}", file=sys.stderr)
        return 2
    results = detect(args.repo)
    if args.json:
        print(json.dumps({
            "repo": str(args.repo.resolve()),
            "detections": results,
        }, indent=2, ensure_ascii=False))
        return 0
    print(f"Profile detection for {args.repo.resolve()}")
    if not results:
        print("No profiles detected.")
        return 0
    for result in results:
        evidence = ", ".join(result["evidence"])
        print(
            f"{result['confidence'].upper():<9} "
            f"{result['dimension']:<10} {result['id']} — {evidence}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
