#!/usr/bin/env python3
"""Gate all docforge documentation work on the analysis it depends on.

Both the knowledge graph and domain graph are required for every docforge
invocation — there is no fallback, no inspection substitute. This script
checks that the two files exist under .ua/ (or the legacy
.understand-anything/) and refuses to report READY unless both are present.
It does not care which tool produced them.

understand-anything is the default producer, but this script also detects a
GitNexus index (.gitnexus/meta.json) and, when the graph is missing but an
index exists, points at the GitNexus bridge (graph_source_gitnexus.py build,
documented in references/gitnexus-bridge.md) instead of only suggesting
/understand. Priority is always: use .ua/*.json if present, regardless of
which source could also build it; only fall back to a source-specific build
suggestion when the files are actually missing. See references/graph-sources.md
for the full capability-to-source dispatch table, and the docstring in
graph_source_gitnexus.py for why this can't be a fully automatic build (MCP
tool calls are agent-mediated, not scriptable).

This script cannot check whether the understand-anything skill/plugin itself
is installed (that's a property of the calling agent's environment, not this
repo's filesystem) — the agent must confirm that separately by checking its
own skill listing or attempting `/understand` and `/understand-domain`.

Exit code 0 only when every file required for the requested --need scope is
present. Non-zero otherwise, with a specific remediation command per gap.

Usage:
    python check_preconditions.py --repo <path> --need graph
    python check_preconditions.py --repo <path> --need domain
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from graph_common import display, show_graph_dirs
from graph_source_gitnexus import detect as gitnexus_detect
from graph_source_ua import detect as ua_detect


GITNEXUS_BUILD_CMD = (
    "    python scripts/graph_source_gitnexus.py build --repo <path> "
    "--nodes <nodes.json> --edges <edges.json> --processes <processes.json>"
)


def print_missing_remediation(repo: Path, gx_index: Path | None, *, is_domain: bool) -> None:
    """Print the Fix: block for a missing graph file. Always shows both
    remediation paths — understand-anything and GitNexus — since either one
    resolves the gap and the user may already have one but not the other
    installed. The GitNexus option's exact steps depend on whether an index
    already exists."""
    if is_domain:
        print("  Fix (understand-anything): after the knowledge graph exists, run:")
        print("    /understand-domain")
        print("  Business flows, docs/flows/, docs/product/overview.md and the "
              "BA/PO overlays are never hand-typed. Do not enumerate flows from "
              "route files or folder names as a substitute for this graph.")
    else:
        print("  Fix (understand-anything): confirm the understand-anything skill is "
              "loaded in this session (check the skill listing, or load/invoke it), "
              "then run:")
        print("    /understand")

    if gx_index:
        print(f"  Fix (GitNexus, index already found at {display(gx_index, repo)}): "
              "follow references/gitnexus-bridge.md, then run:")
        print(GITNEXUS_BUILD_CMD)
    else:
        print("  Fix (GitNexus, not yet installed/indexed): from the repo root, run:")
        print("    npx gitnexus analyze")
        print("    npx gitnexus setup")
        print("  Then follow references/gitnexus-bridge.md and run:")
        print(GITNEXUS_BUILD_CMD)

    if not is_domain:
        print("  Do not proceed to writing documentation from directory names or "
              "guesswork while this is missing.")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", required=True, type=Path)
    ap.add_argument("--need", choices=["graph", "domain"], default="domain",
                     help="'graph' is a partial check (knowledge graph only); 'domain' "
                          "(the default, recommended for every docforge run) checks both "
                          "the knowledge graph and domain graph, which are both required "
                          "for all documentation work — there is no fallback or "
                          "inspection substitute")
    args = ap.parse_args()

    if not args.repo.is_dir():
        print(f"Not a directory: {args.repo}", file=sys.stderr)
        return 2

    ok = True
    ua = ua_detect(args.repo)

    kg = ua["knowledge_graph"]
    if kg:
        print(f"READY  knowledge graph  -> {display(kg, args.repo)}")
    else:
        ok = False
        print("MISSING  knowledge graph  (checked .ua/ and .understand-anything/)")
        show_graph_dirs(args.repo)
        gx = gitnexus_detect(args.repo)
        print_missing_remediation(args.repo, gx["index"], is_domain=False)

    if args.need == "domain":
        dg = ua["domain_graph"]
        if dg:
            print(f"READY  domain graph     -> {display(dg, args.repo)}")
        else:
            ok = False
            print("MISSING  domain graph  (checked .ua/ and .understand-anything/)")
            show_graph_dirs(args.repo)
            gx = gitnexus_detect(args.repo)
            print_missing_remediation(args.repo, gx["index"], is_domain=True)

    print()
    if ok:
        print("All required analysis present. Proceed.")
        return 0
    print("BLOCKED. No documentation of any kind may be written until every "
          "MISSING item above is resolved. Tell the user what is missing and which "
          "command produces it. Both the knowledge graph and domain graph are "
          "required for all docforge work — there is no inspection fallback or "
          "substitute for either.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
