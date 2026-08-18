#!/usr/bin/env python3
"""Harvest decision and concept candidates a run should consider documenting.

`concept` and `adr` are dynamic catalog types gated on `discovered_concept` and
`discovered_decision` -- conditions no code evaluates and, until now, no step
produced. Flows had a harvest pipeline; decisions and concepts had only the
instruction "must be added after discovery", with nothing to discover from. The
result was a `decisions/` and `concepts/` folder holding nothing but an index
explaining its own emptiness.

This produces *candidates only*. Nothing is selected, nothing is written, and
no document is invented: every candidate carries the repository evidence that
suggested it, and the user decides at the write-start selection gate. The
decision signals are the ones `references/decision-records.md` already
prescribes for backfilling, including its five-to-ten ceiling.
"""

from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path

from runtime.common.python._util import dump_json, fail

CANDIDATES_REL = Path(".docforge") / "candidates.json"
SCHEMA_VERSION = "1.0"
# references/decision-records.md: "Backfill five to ten load-bearing ones per
# repo -- enough to cover the architecture a reviewer will ask about -- rather
# than attempting completeness."
DEFAULT_DECISION_LIMIT = 10
DEFAULT_CONCEPT_LIMIT = 8

DEPENDENCY_MANIFESTS = (
    "package.json", "requirements.txt", "pyproject.toml", "Pipfile",
    "go.mod", "Cargo.toml", "pom.xml", "build.gradle", "build.gradle.kts",
    "Gemfile", "composer.json", "mix.exs", "pubspec.yaml", "*.csproj",
)
SOURCE_DIRS = ("src", "lib", "app", "internal", "pkg", "cmd", "services", "packages", "modules")
EXISTING_RECORD_RE = re.compile(r"(?:^|/)(?:adr|adrs|rfc|rfcs|decisions?)/|(?:^|/)(?:ADR|RFC|DESIGN)[-_0-9]", re.IGNORECASE)
SKIP_DIRS = {
    "node_modules", "dist", "build", "target", "vendor", "__pycache__",
    ".git", ".venv", "venv", "coverage", "test", "tests", "spec", "__tests__",
    "fixtures", "migrations", "generated",
}
SOURCE_SUFFIXES = {
    ".py", ".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx", ".go", ".rs", ".java",
    ".kt", ".rb", ".php", ".cs", ".swift", ".c", ".cc", ".cpp", ".h", ".hpp",
    ".scala", ".ex", ".exs", ".dart",
}
# Docforge's own generated trees are output, never evidence.
GENERATED_TREES = ("docs/", "docs-portfolio/", ".docforge/")
# A directory this large is a container, not an idea: descend one level so the
# candidate is `src/lib/kafka` rather than all 304 files under `src/lib`.
CONTAINER_FILE_COUNT = 40
# Below this a directory is too small to carry a concept of its own.
MIN_CLUSTER_FILES = 3
# Trees that hold no mechanism at any depth. Pruned outright: descending finds
# only more of the same, which is how email-template subfolders surfaced as
# architecture "concepts".
PRUNE_TREES = {
    "template", "templates", "mjmltemplates", "asset", "assets", "static",
    "style", "styles", "css", "scss", "img", "images", "icon", "icons",
    "font", "fonts", "locale", "locales", "i18n", "translations",
    "mock", "mocks", "stub", "stubs", "example", "examples", "sample",
    "samples", "snapshot", "snapshots", "seed", "seeds", "script", "scripts",
}
# Names that describe a bag of code rather than an idea. Not emitted as a
# concept, but still descended: `src/lib/kafka` is a real subject even though
# `src/lib` is not. A "utils" or "constants" page is exactly the decorative
# documentation this harvest exists to avoid producing.
NON_CONCEPT_NAMES = {
    "util", "utils", "helper", "helpers", "common", "shared", "misc", "lib",
    "constant", "constants", "enum", "enums", "type", "types", "interface",
    "interfaces", "dto", "dtos", "model", "models", "schema", "schemas",
    "config", "configs", "settings", "doc", "docs", "internal", "core",
}


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug[:60] or "untitled"


def git(repo: Path, *args: str) -> list[str]:
    """Run a read-only git command; an unavailable repo yields no signal."""
    try:
        result = subprocess.run(
            ["git", "-C", str(repo), *args],
            capture_output=True, text=True, timeout=30,
        )
    except (OSError, subprocess.SubprocessError):
        return []
    if result.returncode != 0:
        return []
    return [line for line in result.stdout.splitlines() if line.strip()]


def commit_records(repo: Path, *args: str, limit: int) -> list[dict]:
    lines = git(repo, "log", "--no-merges" if "--merges" not in args else "--merges",
                f"--max-count={limit}", "--date=short",
                "--pretty=format:%H\x1f%ad\x1f%s", *args)
    records = []
    for line in lines:
        parts = line.split("\x1f")
        if len(parts) != 3:
            continue
        commit, date, subject = parts
        records.append({"commit": commit, "date": date, "subject": subject.strip()})
    return records


def dependency_decisions(repo: Path, limit: int) -> list[dict]:
    """Each significant dependency added is a decision (decision-records.md)."""
    out: list[dict] = []
    for pattern in DEPENDENCY_MANIFESTS:
        tracked = git(repo, "ls-files", pattern)
        for path in tracked:
            records = commit_records(repo, "--", path, limit=limit)
            if not records:
                continue
            out.append({
                "kind": "dependency-choice",
                "title": f"Dependency and toolchain choices recorded in {path}",
                "signal": f"{len(records)} tracked change(s) to {path}",
                "evidence": records[:3],
                "paths": [path],
            })
    return out


def root_commit(repo: Path) -> str | None:
    commits = git(repo, "rev-list", "--max-parents=0", "HEAD")
    return commits[-1] if commits else None


def subsystem_decisions(repo: Path, limit: int) -> list[dict]:
    """`git log --diff-filter=A` on major directories: when did each appear?

    A subsystem that arrived in the repository's first commit came with the
    import, not with a decision anyone made here, so it carries no rationale to
    recover and is skipped. Substantial subsystems come first: the point is the
    architecture a reviewer will ask about, not every directory."""
    initial = root_commit(repo)
    out: list[dict] = []
    for count, rel in module_clusters(repo):
        records = commit_records(repo, "--diff-filter=A", "--", rel, limit=limit)
        if not records:
            continue
        introduced = records[-1]
        if initial and introduced["commit"] == initial:
            continue
        out.append({
            "kind": "subsystem-introduced",
            "title": f"Introduce the {rel.rsplit('/', 1)[-1]} subsystem",
            "signal": (
                f"{count} source files under {rel}/, first added "
                f"{introduced['date']} after the initial import"
            ),
            "evidence": [introduced],
            "paths": [rel],
        })
    return out


def reversal_decisions(repo: Path, limit: int) -> list[dict]:
    """A revert or a large merge encodes a decision that was re-argued."""
    out: list[dict] = []
    for record in commit_records(repo, "--grep=^Revert", "--regexp-ignore-case", limit=limit):
        out.append({
            "kind": "reversal",
            "title": record["subject"].removeprefix("Revert ").strip('"'),
            "signal": "a reverted change is a decision that was re-argued",
            "evidence": [record],
            "paths": [],
        })
    return out


def existing_record_decisions(repo: Path) -> list[dict]:
    """An ADR/RFC/design file already in the repo is a decision to migrate.

    Docforge's own output trees are excluded: `docs/architecture/decisions/` is
    what this harvest exists to fill, so reading it back as evidence would let
    a previous empty run justify itself."""
    out: list[dict] = []
    for path in git(repo, "ls-files"):
        if path.startswith(GENERATED_TREES):
            continue
        if EXISTING_RECORD_RE.search(path):
            out.append({
                "kind": "existing-record",
                "title": f"Existing decision material in {path}",
                "signal": "already-written rationale; migrate rather than reconstruct",
                "evidence": [],
                "paths": [path],
            })
    return out


def source_file_count(directory: Path) -> int:
    return sum(
        1 for p in directory.rglob("*")
        if p.is_file()
        and p.suffix in SOURCE_SUFFIXES
        and not any(part in SKIP_DIRS for part in p.relative_to(directory).parts)
    )


def module_clusters(repo: Path) -> list[tuple[int, str]]:
    """Source directories substantial enough to carry an idea, largest first.

    A directory-level signal, not a code-graph one: it says where to look, and
    the agent still judges whether a cross-cutting concept lives there. A
    directory over `CONTAINER_FILE_COUNT` files is replaced by its own
    subdirectories, so a 300-file `src/lib` yields `src/lib/kafka` instead of
    one useless candidate named after the container."""
    def usable(directory: Path) -> bool:
        name = directory.name
        return (
            directory.is_dir()
            and name not in SKIP_DIRS
            and name.lower() not in PRUNE_TREES
            and not name.startswith(".")
        )

    clusters: list[tuple[int, str]] = []
    roots = [repo / name for name in SOURCE_DIRS if (repo / name).is_dir()]
    pending = [child for root in roots for child in sorted(root.iterdir()) if usable(child)]
    while pending:
        directory = pending.pop(0)
        count = source_file_count(directory)
        if count < MIN_CLUSTER_FILES:
            continue
        children = [child for child in sorted(directory.iterdir()) if usable(child)]
        if count > CONTAINER_FILE_COUNT and children:
            pending.extend(children)
            continue
        if directory.name.lower() in NON_CONCEPT_NAMES:
            continue
        clusters.append((count, directory.relative_to(repo).as_posix()))
    clusters.sort(key=lambda item: (-item[0], item[1]))
    return clusters


def concept_candidates(repo: Path, limit: int) -> list[dict]:
    return [
        {
            "kind": "module-cluster",
            "title": rel.rsplit("/", 1)[-1].replace("-", " ").replace("_", " "),
            "signal": f"{count} source files under {rel}/",
            "evidence": [],
            "paths": [rel],
        }
        for count, rel in module_clusters(repo)[:limit]
    ]


def finalize(rows: list[dict], limit: int) -> list[dict]:
    seen: set[str] = set()
    out: list[dict] = []
    for row in rows:
        slug = slugify(row["title"])
        if slug in seen:
            continue
        seen.add(slug)
        out.append({
            "slug": slug,
            "title": row["title"],
            "kind": row["kind"],
            "signal": row["signal"],
            "paths": row["paths"],
            "evidence": row["evidence"],
            "status": "candidate",
        })
        if len(out) >= limit:
            break
    return out


def harvest(repo: Path, decision_limit: int, concept_limit: int) -> dict:
    decisions = finalize(
        existing_record_decisions(repo)
        + dependency_decisions(repo, decision_limit)
        + subsystem_decisions(repo, decision_limit)
        + reversal_decisions(repo, decision_limit),
        decision_limit,
    )
    concepts = finalize(concept_candidates(repo, concept_limit), concept_limit)
    return {
        "version": SCHEMA_VERSION,
        "decisions": decisions,
        "concepts": concepts,
        "summary": {
            "decision_candidates": len(decisions),
            "concept_candidates": len(concepts),
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Harvest decision and concept candidates from repository evidence.",
    )
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--decision-limit", type=int, default=DEFAULT_DECISION_LIMIT)
    parser.add_argument("--concept-limit", type=int, default=DEFAULT_CONCEPT_LIMIT)
    parser.add_argument("--json", action="store_true", help="print the payload instead of writing it")
    args = parser.parse_args(argv)
    repo = args.repo.resolve()
    if not repo.is_dir():
        return fail(f"repository not found: {args.repo}", 2)
    if args.decision_limit < 1 or args.concept_limit < 1:
        return fail("limits must be positive", 2)
    payload = harvest(repo, args.decision_limit, args.concept_limit)
    if args.json:
        print(dump_json(payload), end="")
        return 0
    target = repo / CANDIDATES_REL
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(dump_json(payload), encoding="utf-8")
    print(
        f"{payload['summary']['decision_candidates']} decision and "
        f"{payload['summary']['concept_candidates']} concept candidate(s) -> {CANDIDATES_REL}"
    )
    print("Candidates only: none is selected until the write-start gate.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
