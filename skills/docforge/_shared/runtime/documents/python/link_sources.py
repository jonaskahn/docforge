#!/usr/bin/env python3
"""Expand repo-relative source links into pinned permalinks.

The writer must never hand-assemble a URL containing a 40-character commit sha,
so it writes the readable authoring form:

    ([the crawl-job runner](src/lib/crawler/crawlerjob.js#L397-L399))

and this pass rewrites it, at materialization and again on revise, into an
absolute permalink at the commit the document was grounded against.

Every target is validated first -- the path must exist and the range must be
inside the file -- so a stale reference fails loudly here rather than 404ing for
a reader later. That is the whole point of doing this mechanically: the previous
output carried 1,064 hand-written `path:line` mentions, none of them checked,
all of them pinned to a commit that had already moved.

Read-only unless `--write`. Exit `0` clean, `1` unresolved references, `2` usage.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from runtime.common.python._util import dump_json, fail, load_manifest
from runtime.common.python.repo_identity import blob_url, head_commit, identity_of

# `[label](target)` where the target is a repository-relative source path with an
# optional line fragment. An absolute URL, an anchor, and a `.md` link are all
# left alone: only the authoring form is rewritten.
AUTHORING_LINK = re.compile(
    r"\[(?P<label>[^\]]+)\]\((?P<path>(?!https?://|mailto:|#|/)[A-Za-z0-9_][A-Za-z0-9_./-]*"
    r"\.(?:c|cc|cpp|cs|go|java|js|jsx|json|mjs|properties|py|rb|rs|swift|toml|ts|tsx|xml|ya?ml|sh|sql|tf)"
    r")(?P<fragment>#L(?P<start>\d+)(?:-L?(?P<end>\d+))?)?\)"
)
FENCE = re.compile(r"^\s{0,3}(`{3,}|~{3,})")
# A path or `file.ext:line` as the visible text defeats the purpose: the reader
# is owed a readable noun phrase, and the URL already carries the location.
PATH_LABEL = re.compile(
    r"^[A-Za-z0-9_./-]*\.(?:c|cc|cpp|cs|go|java|js|jsx|json|mjs|py|rb|rs|swift|toml|ts|tsx|xml|ya?ml)"
    r"(?::\d+(?:-\d+)?)?$"
)


def fenced_lines(text: str) -> set[int]:
    """Line numbers inside a fence, which this pass never rewrites."""
    inside: set[int] = set()
    marker: str | None = None
    for number, line in enumerate(text.splitlines(), 1):
        match = FENCE.match(line)
        if match:
            if marker is None:
                marker = match.group(1)
                inside.add(number)
                continue
            if line.strip().startswith(marker):
                inside.add(number)
                marker = None
                continue
        if marker is not None:
            inside.add(number)
    return inside


def line_count(path: Path) -> int:
    try:
        return len(path.read_bytes().splitlines())
    except OSError:
        return 0


def expand(
    text: str,
    repo: Path,
    identity: dict,
    commit: str,
) -> tuple[str, list[str]]:
    """Rewrite every authoring-form source link; report the ones that cannot be."""
    protected = fenced_lines(text)
    problems: list[str] = []
    out_lines: list[str] = []

    for number, line in enumerate(text.splitlines(keepends=True), 1):
        if number in protected:
            out_lines.append(line)
            continue

        def replace(match: re.Match) -> str:
            rel = match.group("path")
            label = match.group("label")
            target = repo / rel
            if not target.is_file():
                problems.append(f"line {number}: no such file: {rel}")
                return match.group(0)
            if PATH_LABEL.match(label.strip("`")):
                problems.append(
                    f"line {number}: link text {label!r} is a path; name the thing, not its location"
                )
                return match.group(0)
            start = match.group("start")
            end = match.group("end")
            if start is None:
                return f"[{label}]({blob_url(identity, commit, rel)})"
            first, last = int(start), int(end or start)
            if first < 1 or last < first:
                problems.append(f"line {number}: invalid range L{first}-{last} for {rel}")
                return match.group(0)
            total = line_count(target)
            if last > total:
                problems.append(
                    f"line {number}: {rel} has {total} lines; range L{first}-{last} is out of bounds"
                )
                return match.group(0)
            return f"[{label}]({blob_url(identity, commit, rel, first, last)})"

        out_lines.append(AUTHORING_LINK.sub(replace, line))

    return "".join(out_lines), problems


def stamp_commit(repo: Path, doc_path: str, commit: str) -> None:
    """Record the pinned commit in the document's provenance sidecar.

    Best-effort: a document whose sidecar entry does not exist yet is being
    written for the first time and gets its commit when provenance is stamped."""
    from runtime.common.python import provenance_store as store

    entry = store.entry_for(repo, doc_path)
    if not isinstance(entry, dict):
        return
    provenance = entry.get("provenance")
    if not isinstance(provenance, dict):
        return
    if provenance.get("git_commit") == commit:
        return
    provenance["git_commit"] = commit
    store.write_entry(repo, doc_path, entry)


def document_paths(manifest: dict, repo: Path) -> list[Path]:
    from runtime.common.python.agent_context import AGENT_CONTEXT_GROUP

    paths = []
    for doc in manifest.get("documents", []):
        # Agent-context outputs carry no links or URLs of any kind; expanding
        # one would breach an isolation boundary the audit enforces.
        if doc.get("group") == AGENT_CONTEXT_GROUP:
            continue
        path = doc.get("path", "")
        if path.endswith(".md") and (repo / path).is_file():
            paths.append(repo / path)
    return paths


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Expand repo-relative source links into pinned permalinks.",
    )
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--file", type=Path, action="append", default=[])
    parser.add_argument("--commit", help="pin to this commit instead of HEAD")
    parser.add_argument("--write", action="store_true", help="rewrite files in place")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    repo = args.repo.resolve()
    if not repo.is_dir():
        return fail(f"repository not found: {args.repo}", 2)
    if not args.manifest and not args.file:
        return fail("pass --manifest or at least one --file", 2)

    manifest = {}
    if args.manifest:
        try:
            manifest = load_manifest(args.manifest)
        except ValueError as exc:
            return fail(str(exc), 2)

    identity = identity_of(manifest)
    if identity is None:
        return fail(
            "project.repository is not declared; source links stay in their authoring "
            "form until a repository web base is declared "
            "(manage_manifest set-repository)",
            2,
        )
    commit = args.commit or head_commit(repo)
    if commit is None:
        return fail("cannot resolve a commit to pin to; pass --commit", 2)

    targets = [path.resolve() for path in args.file] or document_paths(manifest, repo)
    changed: list[str] = []
    problems: list[str] = []
    for path in targets:
        if not path.is_file():
            problems.append(f"{path}: not a file")
            continue
        original = path.read_text(encoding="utf-8")
        updated, issues = expand(original, repo, identity, commit)
        problems.extend(f"{path.relative_to(repo)}: {issue}" for issue in issues)
        if updated != original:
            rel = str(path.relative_to(repo))
            changed.append(rel)
            if args.write:
                path.write_text(updated, encoding="utf-8")
                # `provenance.git_commit` has been schema-declared and validated
                # since 2.0 but was never produced. Stamp it here: it names the
                # commit this document's links resolve against, so a reader who
                # finds a stale link can see exactly which revision it pinned.
                stamp_commit(repo, rel, commit)

    payload = {
        "commit": commit,
        "web_base": identity["web_base"],
        "forge": identity["forge"],
        "expanded": sorted(changed),
        "problems": sorted(problems),
        "written": bool(args.write),
    }
    if args.json:
        print(dump_json(payload), end="")
    else:
        verb = "expanded" if args.write else "would expand"
        print(f"{verb} source links in {len(changed)} document(s) at {commit[:12]}")
        for item in payload["expanded"]:
            print(f"  {item}")
        if problems:
            print(f"\nUNRESOLVED ({len(problems)})")
            for item in payload["problems"]:
                print(f"  {item}")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
