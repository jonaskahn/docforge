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
    for rel in candidates:
        p = repo / rel
        if p.is_file():
            return p
    return None


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
        print(f"READY  knowledge graph  -> {kg.relative_to(args.repo)}")
    else:
        ok = False
        print("MISSING  knowledge graph  (checked .ua/ and .understand-anything/)")
        print("  Fix: confirm the understand-anything skill is available in this "
              "session (check the skill listing, or try invoking it), then run:")
        print("    /understand")
        print("  Do not proceed to writing documentation from directory names or "
              "guesswork while this is missing.")

    if args.need == "domain":
        dg = find(args.repo, DOMAIN_GRAPH_CANDIDATES)
        if dg:
            print(f"READY  domain graph     -> {dg.relative_to(args.repo)}")
        else:
            ok = False
            print("MISSING  domain graph  (checked .ua/ and .understand-anything/)")
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
