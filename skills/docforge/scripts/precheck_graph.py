#!/usr/bin/env python3
"""Gate docforge documentation work on the graph analysis it depends on —
provider-agnostic, over whatever graph sources are registered in
graph_source_registry.py (understand-anything, GitNexus, and any future source).

Two capabilities matter:

  code_graph  — structure and call/import relationships. **Universal precondition.**
                Docforge does nothing without one, but *any* single registered
                source that has built one satisfies it; docforge never
                fabricates a code graph itself.

  flow_graph  — business flows and ordered steps. Needed only when a selected
                catalog entry declares it. Resolved native-first (a source
                that emits flows — understand-anything's flow data, or
                GitNexus's native processes), else docforge derives a
                provisional one from the code graph into
                .docforge/tmp/flow-graph.json (never committed — see
                derive_flow_graph.py). So flow docs are never hard-blocked while
                a code graph exists.

This script only inspects the filesystem; it cannot tell whether a producer
plugin/skill is installed in the calling agent's environment — the agent
confirms that separately (skill listing) using the setup hints printed here.

When more than one source is ready for the same repo, this reports **all** of
them (with each one's read mechanism) so the agent can choose by the provider
fit documented in references/graph-sources.md.

Exit code 0 when the requested --need scope is satisfiable; non-zero otherwise,
with per-source remediation.

Usage:
    python precheck_graph.py --repo <path>                 # --need code (default)
    python precheck_graph.py --repo <path> --need flow
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from graph_storage import relative_display_path, find_graph_file, list_known_graph_dirs
from graph_source_registry import setup_hints_for_missing, resolve_all_ready

DERIVED_FLOW_CANDIDATES = [".docforge/tmp/flow-graph.json"]

# How each source's graph is read, keyed by its read_mode, for the report.
READ_MECHANISM = {
    "json": "JSON on disk — read with read_graph.py",
    "db": "ladybug DB — query via the gitnexus MCP, or offline with "
          "graph_source_gitnexus_reader.py",
    "mcp": "SQLite index — query via the codegraph MCP tool (codegraph_explore); "
           "no offline reader — confirm it is wired to this session first, else "
           "`codegraph install`",
}


def print_setup_hints(repo: Path, capability: str) -> None:
    """Print every capable source's remediation block for a missing graph."""
    for src, lines in setup_hints_for_missing(repo, capability):
        for line in lines:
            print(line if line.startswith("    ") else f"  {line}")


def check_code_graph(repo: Path) -> bool:
    """Report every source that has a code graph ready. True if at least one is."""
    ready = resolve_all_ready(repo, "code_graph")
    if not ready:
        print("MISSING  code graph   (no registered source has one built)")
        list_known_graph_dirs(repo)
        print("  Build a code graph from any one configured source, then re-run. Options:")
        print_setup_hints(repo, "code_graph")
        print("  Do not write documentation from directory names or guesswork while this is missing.")
        return False
    for src, path in ready:
        mechanism = READ_MECHANISM.get(src.get("read_mode", ""), "")
        suffix = f"  [{mechanism}]" if mechanism else ""
        state = src["detect"](repo)
        if state.get("stale") is True:
            suffix += "  [STALE vs HEAD; refresh requires approval]"
        print(f"READY    code graph   -> {relative_display_path(path, repo)}  "
              f"(source: {src['name']}){suffix}")
    if len(ready) > 1:
        print(f"  {len(ready)} sources are ready — ask the user which should be "
              "primary; select by the evidence need in references/graph-sources.md.")
    return True


def report_flow_graph(repo: Path) -> str:
    """Resolve the flow graph. Returns 'native', 'derived', or 'none' and
    prints a status line. Does not itself decide the exit code."""
    ready = resolve_all_ready(repo, "flow_graph")
    if ready:
        for src, path in ready:
            print(f"READY    flow graph   -> {relative_display_path(path, repo)}  "
                  f"(source: {src['name']}, authoritative)")
        return "native"
    derived = find_graph_file(repo, DERIVED_FLOW_CANDIDATES)
    if derived:
        print(f"READY    flow graph   -> {relative_display_path(derived, repo)}  "
              "(docforge-derived, provisional)")
        return "derived"
    print("MISSING  flow graph   (no native flow graph; none derived yet)")
    return "none"


def print_flow_remediation(repo: Path) -> None:
    print("  A selected catalog entry requires the flow graph. Resolve either way:")
    print("  (a) Derive a provisional flow graph from the code graph "
          "(see references/flow-derivation.md):")
    print("    python scripts/derive_flow_graph.py prepare --repo <path>")
    print("    # dispatch the docforge domain analyzer on the emitted context, then")
    print("    python scripts/derive_flow_graph.py write --repo <path> --analysis <analysis.json>")
    print("    # writes .docforge/tmp/flow-graph.json — provisional, never committed")
    print("  (b) Or produce a native (authoritative) flow graph from a source:")
    print_setup_hints(repo, "flow_graph")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", required=True, type=Path)
    ap.add_argument("--need", default="code", choices=["code", "flow"],
                    help="'code' (default): the universal code-graph gate. "
                         "'flow': also require a flow graph (native or derived).")
    args = ap.parse_args()

    need = args.need
    if not args.repo.is_dir():
        print(f"Not a directory: {args.repo}", file=sys.stderr)
        return 2

    code_ok = check_code_graph(args.repo)
    flow_state = report_flow_graph(args.repo) if (need == "flow" or code_ok) else "none"

    print()
    if not code_ok:
        print("BLOCKED. A code graph is docforge's universal precondition — no "
              "documentation of any kind may be written until one exists. Tell the "
              "user which source to build it with (options above); docforge never "
              "fabricates a code graph itself.")
        return 1

    if need == "code":
        print("Code graph present — proceed.")
        if flow_state == "none":
            print("Note: no flow graph yet. Selected flow, Business Analyst, and "
                  "agent flow/glossary documents will resolve it when reached "
                  "(--need flow); other documents may proceed.")
        return 0

    # need == "flow"
    if flow_state != "none":
        print("Code and flow graphs present — proceed.")
        if flow_state == "derived":
            print("Note: flows are docforge-derived (provisional). Confirm business "
                  "rules against source before asserting them; a native flow graph is "
                  "authoritative where available.")
        return 0

    print("Code graph present, but flows are required for this plan and none exist yet.")
    print_flow_remediation(args.repo)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
