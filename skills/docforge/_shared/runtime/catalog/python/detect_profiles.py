#!/usr/bin/env python3
"""Detect Docforge shape, platform, framework, and concern profile candidates."""

from __future__ import annotations

import argparse
import fnmatch
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

from . import discovery_gate
from runtime.common.python import manifest_deps
from . import query_catalog

SKILL_ROOT = Path(__file__).resolve().parent.parent.parent.parent
DIMENSIONS = ["shapes", "platforms", "frameworks", "concerns"]
IGNORED = {
    ".git", ".codegraph", ".gitnexus", ".docforge", "node_modules",
    ".build", "build", "dist", "DerivedData", ".venv", "venv", "__pycache__",
}
MAX_FILES = 25000
MAX_CONTENT_BYTES = 1024 * 1024
MAX_TOTAL_CONTENT_BYTES = 32 * 1024 * 1024
MAX_EVIDENCE = 20
MAX_EXCERPTS = 8
MAX_EXCERPT_CHARS = 400
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


def glob_regex(pattern: str) -> re.Pattern[str]:
    expression = []
    index = 0
    while index < len(pattern):
        char = pattern[index]
        if char == "*" and index + 1 < len(pattern) and pattern[index + 1] == "*":
            expression.append(".*")
            index += 2
        elif char == "*":
            expression.append("[^/]*")
            index += 1
        elif char == "?":
            expression.append("[^/]")
            index += 1
        else:
            expression.append(re.escape(char))
            index += 1
    return re.compile(f"^{''.join(expression)}$")


def matches_path(relative: str, pattern: str) -> bool:
    patterns = [pattern]
    if pattern.startswith("**/"):
        patterns.append(pattern[3:])
    basename = PurePosixPath(relative).name
    for candidate in patterns:
        regex = glob_regex(candidate)
        if regex.match(relative):
            return True
        if "/" not in candidate and regex.match(basename):
            return True
    return False


def signal_strength(signal: dict) -> str:
    explicit = signal.get("strength")
    if explicit in {"strong", "weak"}:
        return explicit
    kind = signal.get("kind")
    if kind == "dependency":
        return "strong"
    if kind == "content":
        return "weak"
    return "strong"


def cue_for_signal(signal: dict, relative: str = "") -> str:
    kind = signal.get("kind")
    if kind == "dependency":
        return f"dep:{signal.get('ecosystem', '')}:{signal.get('name', '')}"
    if kind == "content":
        token = (signal.get("contains") or "content").strip().lower().replace(" ", "-")
        return f"content:{token[:48]}"
    pattern = signal.get("pattern") or ""
    parts = [part for part in pattern.replace("**/", "").split("/") if part and "*" not in part]
    if parts:
        return f"path:{parts[-1].lower()}"
    if relative:
        fragments = [part for part in PurePosixPath(relative).parts if part not in {".", ".."}]
        if fragments:
            return f"path:{fragments[-2].lower() if len(fragments) > 1 else fragments[0].lower()}"
    return "path:unknown"


def inventory(repo: Path) -> list[tuple[str, Path]]:
    """Collect files under `repo` for profile-signal matching. Stops short of
    a nested repository's own contents — a subdirectory that is itself a
    separate git repository (its own .git dir or file, the same marker a
    submodule worktree uses) is a distinct project; its source must not be
    blended into this repo's own profile evidence."""
    found: list[tuple[str, Path]] = []

    def walk(directory: Path) -> None:
        if len(found) >= MAX_FILES:
            return
        for path in sorted(directory.iterdir(), key=lambda item: item.name):
            if path.name in IGNORED or path.is_symlink():
                continue
            if path.is_dir():
                git_marker = path / ".git"
                if git_marker.is_dir() or git_marker.is_file():
                    continue  # nested repo boundary; its evidence is its own
                walk(path)
            elif path.is_file():
                found.append((path.relative_to(repo).as_posix(), path))
            if len(found) >= MAX_FILES:
                return

    walk(repo)
    return found


def detect(
    repo: Path,
    *,
    persist: bool = True,
    files: list[tuple[str, Path]] | None = None,
) -> list[dict]:
    """Pass `files` to reuse an `inventory(repo)` the caller already has —
    the walk is the expensive part, and several callers need both."""
    profiles = query_catalog.load_profiles()
    if files is None:
        files = inventory(repo)
    dependencies = manifest_deps.extract_dependencies(files)
    if persist:
        persist_manifest_deps(repo, dependencies)
    cache: dict[Path, str] = {}
    cached_bytes = 0
    results: list[dict] = []
    for dimension in DIMENSIONS:
        for profile in profiles[dimension]:
            evidence: list[str] = []
            matched_strengths: set[str] = set()
            cues: list[str] = []
            for signal in profile.get("signals", []):
                strength = signal_strength(signal)
                if signal["kind"] == "dependency":
                    ecosystem = signal.get("ecosystem", "")
                    key = manifest_deps.normalize(ecosystem, signal.get("name", ""))
                    for manifest_path in dependencies.get(ecosystem, {}).get(key, []):
                        evidence.append(manifest_path)
                        matched_strengths.add(strength)
                        cues.append(cue_for_signal(signal))
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
                    matched_strengths.add(strength)
                    cues.append(cue_for_signal(signal, relative))
            evidence = sorted(set(evidence))
            if not evidence:
                continue
            cue_list = sorted(set(cues))
            has_strong = "strong" in matched_strengths
            match_strength = "strong" if has_strong else "weak"
            confidence = "confirmed" if has_strong else "candidate"
            results.append({
                "dimension": dimension,
                "id": profile["id"],
                "confidence": confidence,
                "evidence": evidence[:MAX_EVIDENCE],
                "match_strength": match_strength,
                "cues": cue_list,
                "ambiguous_with": [],
            })
    _attach_ambiguous_with(results)
    return results


def _attach_ambiguous_with(results: list[dict]) -> None:
    by_cue: dict[str, list[dict]] = {}
    for item in results:
        for cue in item.get("cues", []):
            if cue.startswith("path:") or cue.startswith("content:"):
                by_cue.setdefault(cue, []).append(item)
    for item in results:
        peers = []
        seen = set()
        for cue in item.get("cues", []):
            for peer in by_cue.get(cue, []):
                key = (peer["dimension"], peer["id"])
                if key == (item["dimension"], item["id"]) or key in seen:
                    continue
                if peer.get("match_strength") == "strong" and item.get("match_strength") == "strong":
                    continue
                seen.add(key)
                peers.append({
                    "dimension": peer["dimension"],
                    "id": peer["id"],
                    "confidence": peer["confidence"],
                    "cue": cue,
                })
        peers.sort(key=lambda row: (row["dimension"], row["id"], row.get("cue", "")))
        item["ambiguous_with"] = peers


def _dependency_summary(dependencies: dict) -> dict:
    summary = {}
    for ecosystem in sorted(dependencies):
        summary[ecosystem] = sorted(dependencies[ecosystem].keys())
    return summary


def _excerpts(repo: Path, evidence_paths: list[str], files: list[tuple[str, Path]]) -> list[dict]:
    index = {relative: path for relative, path in files}
    excerpts = []
    for relative in evidence_paths:
        if len(excerpts) >= MAX_EXCERPTS:
            break
        path = index.get(relative)
        if path is None:
            continue
        if path.suffix.lower() not in TEXT_SUFFIXES and path.name not in TEXT_NAMES:
            continue
        try:
            size = path.stat().st_size
        except OSError:
            continue
        if size > MAX_CONTENT_BYTES:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")[:MAX_EXCERPT_CHARS]
        excerpts.append({"path": relative, "text": text, "max_chars": MAX_EXCERPT_CHARS})
    return excerpts


def emit_gate_pack(repo: Path) -> dict:
    profiles = query_catalog.load_profiles()
    files = inventory(repo)
    dependencies = manifest_deps.extract_dependencies(files)
    detections = detect(repo, files=files)
    strong = [item for item in detections if item["confidence"] == "confirmed"]
    weak = [item for item in detections if item["confidence"] == "candidate"]
    cue_map: dict[str, dict] = {}
    for item in detections:
        for cue in item.get("cues", []):
            bucket = cue_map.setdefault(cue, {
                "cue": cue,
                "surface": item["evidence"][0] if item["evidence"] else cue,
                "kind": "dependency" if cue.startswith("dep:") else (
                    "content_keyword" if cue.startswith("content:") else "path_fragment"
                ),
                "candidate_profiles": [],
            })
            entry = {
                "dimension": item["dimension"],
                "id": item["id"],
                "why": (
                    "strong signal"
                    if item.get("match_strength") == "strong"
                    else "weak path or content signal"
                ),
            }
            if entry not in bucket["candidate_profiles"]:
                bucket["candidate_profiles"].append(entry)
    # Offer persistence / ai-ml as peers for shared path nouns when weak cues fire.
    peer_concerns = ["persistence", "ai-ml"]
    for cue, bucket in cue_map.items():
        if not cue.startswith("path:"):
            continue
        present = {(row["dimension"], row["id"]) for row in bucket["candidate_profiles"]}
        for concern_id in peer_concerns:
            key = ("concerns", concern_id)
            if key in present:
                continue
            bucket["candidate_profiles"].append({
                "dimension": "concerns",
                "id": concern_id,
                "why": "catalog concern available; unconfirmed",
            })
    cues = sorted(cue_map.values(), key=lambda row: row["cue"])
    for bucket in cues:
        bucket["candidate_profiles"].sort(key=lambda row: (row["dimension"], row["id"]))
    evidence_paths = []
    for item in detections:
        for path in item["evidence"]:
            if path not in evidence_paths:
                evidence_paths.append(path)
    catalog_ids = {
        dimension: sorted(profile["id"] for profile in profiles[dimension])
        for dimension in [*DIMENSIONS, "audiences"]
    }
    query_hints = {}
    for dimension in DIMENSIONS:
        for profile in profiles[dimension]:
            if profile.get("query_hints"):
                query_hints[profile["id"]] = list(profile["query_hints"])
    # Side effect for WRITE: tech-stack reads this scratch instead of re-deriving.
    persist_manifest_deps(repo, dependencies)
    # Lazy import: common.scale imports this module, so a module-level import
    # here would be circular. The pack reuses the same walk and extraction.
    from runtime.common.python import scale as scale_module

    return {
        "repo": str(repo.resolve()),
        "detections": detections,
        "strong_detections": strong,
        "weak_detections": weak,
        "cues": cues,
        "excerpts": _excerpts(repo, evidence_paths, files),
        "dependencies": _dependency_summary(dependencies),
        "scale": scale_module.compute_scale(repo, files=files, detections=detections, dependencies=dependencies),
        "catalog_ids": catalog_ids,
        "query_hints": query_hints,
        "cue_hints": query_catalog.load_index().get("cue_hints", []),
        "needs_gate": discovery_gate.needs_gate(detections, cues),
    }


def persist_manifest_deps(repo: Path, dependencies: dict) -> Path:
    """Write manifest dependency rows for the tech-stack WRITE step."""
    scratch = repo / ".docforge" / "scratch"
    scratch.mkdir(parents=True, exist_ok=True)
    path = scratch / "manifest-deps.json"
    path.write_text(
        json.dumps(
            {
                "generated_at": datetime.now(timezone.utc)
                .replace(microsecond=0)
                .isoformat(),
                "dependencies": dependencies,
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--json", action="store_true")
    parser.add_argument(
        "--emit-gate-pack",
        action="store_true",
        help="emit bounded discovery gate pack for agent interpretation",
    )
    args = parser.parse_args()
    if not args.repo.is_dir():
        print(f"error: not a directory: {args.repo}", file=sys.stderr)
        return 2
    if args.emit_gate_pack:
        print(json.dumps(emit_gate_pack(args.repo), indent=2, ensure_ascii=False))
        return 0
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
            f"{result['dimension']:<10} {result['id']} "
            f"[{result['match_strength']}] — {evidence}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
