#!/usr/bin/env python3
"""Gate flow/domain documentation work on the analysis it depends on.

Business flows are never hand-typed — they come from the understand-anything
domain graph. This script is the mechanical half of that rule: it checks the
two files that pipeline produces and refuses to report READY unless both are
present. It cannot check whether the understand-anything skill/plugin itself
is installed (that's a property of the calling agent's environment, not this
repo's filesystem) — the agent must confirm that separately by checking its
own skill listing or attempting `/understand`.

Exit code 0 only when every file required for the requested `--need` scope is
present. Non-zero otherwise, with a specific remediation command per gap.

Usage:
    python check_preconditions.py --repo <path> --need graph
    python check_preconditions.py --repo <path> --need domain
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

KNOWLEDGE_GRAPH_CANDIDATES = [
    ".ua/knowledge-graph.json",
    ".understand-anything/knowledge-graph.json",
]

DOMAIN_GRAPH_CANDIDATES = [
    ".ua/domain-graph.json",
    ".understand-anything/domain-graph.json",
]


def find(repo: Path, candidates: list[str]) -> Path | None:
    """Search the graph at the repo root.

    The graphs live at the project root ($PROJECT_ROOT/.ua/...). If --repo happens to
    point at a subdirectory, a direct lookup would report "not found" even
    though the file exists at the root, so search the given directory and every
    ancestor up to (and including) the git root.
    """
    base = repo.resolve()
    for cur in (base, *base.parents):
        for rel in candidates:
            p = cur / rel
            if p.is_file():
                return p
        if (cur / ".git").exists():
            break  # reached the repo root; do not climb past it
    return None


def display(found: Path, repo: Path) -> str:
    """Path relative to --repo when possible, else absolute (graph may sit at an
    ancestor when --repo is a subdirectory)."""
    try:
        return str(found.relative_to(repo.resolve()))
    except ValueError:
        return str(found)


def show_graph_dirs(repo: Path) -> None:
    """On a miss, list what the graph folders actually hold so a false 'not
    found' (folder present, expected file absent or misnamed) is visible at a
    glance. Points at validate_graphs.py for the full probe."""
    base = repo.resolve()
    listed = False
    for cur in (base, *base.parents):
        for name in (".ua", ".understand-anything"):
            d = cur / name
            if d.is_dir():
                try:
                    names = sorted(p.name for p in d.iterdir())
                except OSError as e:
                    names = [f"(error listing: {e})"]
                print(f"  {name}/ exists at {display(d, repo)} — contains: "
                      f"{', '.join(names) or '(empty)'}")
                listed = True
        if (cur / ".git").exists():
            break
    if listed:
        print("  Diagnose: python scripts/validate_graphs.py --repo . --verbose")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", required=True, type=Path)
    ap.add_argument("--need", choices=["graph", "domain"], default="domain",
                     help="'graph' checks only the knowledge graph (architecture work); "
                          "'domain' also checks the domain graph (required for any flow, "
                          "product/overview, or business-analyst/product-owner work)")
    args = ap.parse_args()

    if not args.repo.is_dir():
        print(f"Not a directory: {args.repo}", file=sys.stderr)
        return 2

    ok = True

    kg = find(args.repo, KNOWLEDGE_GRAPH_CANDIDATES)
    if kg:
        print(f"READY  knowledge graph  -> {display(kg, args.repo)}")
    else:
        ok = False
        print("MISSING  knowledge graph  (checked .ua/ and .understand-anything/)")
        show_graph_dirs(args.repo)
        print("  Fix: confirm the understand-anything skill is loaded in this session "
              "(check the skill listing, or load/invoke it), then run:")
        print("    /understand")
        print("  Do not proceed to writing documentation from directory names or "
              "guesswork while this is missing.")

    if args.need == "domain":
        dg = find(args.repo, DOMAIN_GRAPH_CANDIDATES)
        if dg:
            print(f"READY  domain graph     -> {display(dg, args.repo)}")
        else:
            ok = False
            print("MISSING  domain graph  (checked .ua/ and .understand-anything/)")
            show_graph_dirs(args.repo)
            print("  Fix: after the knowledge graph exists, run:")
            print("    /understand-domain")
            print("  Business flows, docs/flows/, docs/product/overview.md and the "
                  "BA/PO overlays are never hand-typed. Do not enumerate flows from "
                  "route files or folder names as a substitute for this graph.")

    print()
    if ok:
        print("All required analysis present. Proceed.")
        return 0
    print("BLOCKED. Do not write flow, product, or BA/PO documentation until every "
          "MISSING item above is resolved. Tell the user what is missing and which "
          "command produces it; do not silently fall back to inspection for this "
          "scope — that fallback is reserved for architecture/spine documents "
          "under non-negotiable 1, not for flows.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
