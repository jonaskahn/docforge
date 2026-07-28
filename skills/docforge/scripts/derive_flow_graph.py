#!/usr/bin/env python3
"""Docforge's own flow-graph derivation — build a provisional domain/flow graph
from an existing code graph when no native flow graph is available.

Docforge needs a flow graph for docs/flows/, docs/product/, the BA/PO overlays,
and agent-context flow sections. When a source supplies one natively (an
understand-anything domain graph, or GitNexus's native processes) docforge uses
that. When none exists — a code-graph-only source with no flow data — docforge
derives one *from the code graph it already has*, grounded in the graph and
never invented, and writes it to .docforge/tmp/domain-graph.json: provisional,
git-ignored, regenerated each run, never committed.

The reasoning step is agent-mediated (a script cannot infer business domains):

    python derive_flow_graph.py prepare --repo <path>
    # -> writes .docforge/tmp/domain-context.json (compact code-graph digest)
    # The agent dispatches the docforge domain analyzer on that context per
    # references/domain-derivation.md and saves its JSON to <analysis.json>.
    python derive_flow_graph.py write --repo <path> --analysis <analysis.json>
    # -> validates and writes .docforge/tmp/domain-graph.json (+ .gitignore)

Docforge's flow shape:
    { "derived": true, "source": "<code-graph source>",
      "generatedFrom": "<code-graph path>", "generatedAt": "<iso>",
      "flows": [ { "name", "domain"?, "entryPoint"?,
                   "steps": [ { "order", "name", "path"? } ] } ] }
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from graph_storage import ensure_tmp_dir_gitignored, validate_flow_graph_shape, write_flow_graph
from graph_source_registry import resolve_first_ready

TMP_REL = ".docforge/tmp"
CONTEXT_NAME = "domain-context.json"

# Loose key probing — the code-graph schema varies by source, so search rather
# than assume (mirrors read_graph.py's tolerance).
NODE_KEYS = ["nodes", "files", "entities", "items"]
EDGE_KEYS = ["edges", "links", "relationships", "relations"]
ID_KEYS = ["id", "nodeId", "key", "name"]
PATH_KEYS = ["path", "filePath", "file", "relativePath", "location"]
LABEL_KEYS = ["name", "label", "title", "symbol"]
KIND_KEYS = ["type", "kind", "nodeType", "category"]
SUMMARY_KEYS = ["summary", "description", "explanation", "doc"]
SRC_KEYS = ["source", "from", "src", "start"]
DST_KEYS = ["target", "to", "dst", "end"]
EDGEKIND_KEYS = ["type", "kind", "relation", "label"]
# Edge kinds that carry flow/structure signal for the analyzer.
FLOW_EDGE_HINTS = ("call", "import", "contain", "handle", "route", "step", "entry")


def first_present(node: dict, keys: list[str]):
    for key in keys:
        if isinstance(node, dict) and key in node and node[key] not in (None, ""):
            return node[key]
    return None


def locate_collection(doc, keys: list[str], depth: int = 3):
    if not isinstance(doc, dict) or depth < 0:
        return []
    for key in keys:
        value = doc.get(key)
        if isinstance(value, list) and (not value or isinstance(value[0], dict)):
            return value
        if isinstance(value, dict):
            entries = list(value.values())
            if entries and isinstance(entries[0], dict):
                return entries
    for value in doc.values():
        if isinstance(value, dict):
            found = locate_collection(value, keys, depth - 1)
            if found:
                return found
    return []


def load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise ValueError(f"file not found: {path}")
    except json.JSONDecodeError as error:
        raise ValueError(f"invalid JSON in {path}: {error}")


def build_context(repo: Path):
    source, path = resolve_first_ready(repo, "code_graph")
    if not path:
        raise ValueError(
            "no code graph found — derivation needs one to work from. Run "
            "precheck_graph.py --need code for how to build it."
        )
    doc = load_json(path)
    nodes = locate_collection(doc, NODE_KEYS)
    edges = locate_collection(doc, EDGE_KEYS)

    slim_nodes = []
    for node in nodes:
        slim_nodes.append({
            "id": first_present(node, ID_KEYS),
            "name": first_present(node, LABEL_KEYS),
            "type": first_present(node, KIND_KEYS),
            "path": first_present(node, PATH_KEYS),
            "summary": first_present(node, SUMMARY_KEYS),
        })
    slim_edges = []
    for edge in edges:
        kind = str(first_present(edge, EDGEKIND_KEYS) or "").lower()
        if not any(hint in kind for hint in FLOW_EDGE_HINTS):
            continue
        slim_edges.append({
            "source": first_present(edge, SRC_KEYS),
            "target": first_present(edge, DST_KEYS),
            "type": first_present(edge, EDGEKIND_KEYS),
        })

    layers = doc.get("layers") if isinstance(doc.get("layers"), list) else []
    return {
        "generatedFrom": str(path),
        "source": source["name"] if source else None,
        "repo": repo.resolve().name,
        "nodeCount": len(slim_nodes),
        "edgeCount": len(slim_edges),
        "nodes": slim_nodes,
        "edges": slim_edges,
        "layers": layers,
    }


def run_prepare(args: argparse.Namespace) -> int:
    try:
        context = build_context(args.repo)
    except ValueError as error:
        print(f"PREPARE FAILED: {error}", file=sys.stderr)
        return 1
    ensure_tmp_dir_gitignored(args.repo)
    out = args.repo.resolve() / TMP_REL / CONTEXT_NAME
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(context, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {out} ({context['nodeCount']} nodes, {context['edgeCount']} flow-signal edges, "
          f"source: {context['source']})")
    print("Next: dispatch the docforge domain analyzer on this context "
          "(references/domain-derivation.md), save its JSON, then run:")
    print(f"    python scripts/derive_flow_graph.py write --repo {args.repo} --analysis <analysis.json>")
    return 0


def run_write(args: argparse.Namespace) -> int:
    try:
        analysis = load_json(args.analysis)
    except ValueError as error:
        print(f"WRITE FAILED: {error}", file=sys.stderr)
        return 1

    if not isinstance(analysis, dict):
        print("WRITE FAILED: analysis must be a JSON object with a 'flows' list", file=sys.stderr)
        return 1

    context_src = None
    context_path = None
    context_file = args.repo.resolve() / TMP_REL / CONTEXT_NAME
    if context_file.is_file():
        try:
            context = json.loads(context_file.read_text(encoding="utf-8"))
            context_src = context.get("source")
            context_path = context.get("generatedFrom")
        except (OSError, json.JSONDecodeError):
            pass

    flow_graph = {
        "derived": True,
        "source": analysis.get("source") or context_src,
        "generatedFrom": analysis.get("generatedFrom") or context_path,
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "flows": analysis.get("flows"),
    }
    if "domains" in analysis:
        flow_graph["domains"] = analysis["domains"]

    error = validate_flow_graph_shape(flow_graph)
    if error:
        print(f"WRITE FAILED: {error}. The analyzer must return a non-empty "
              "'flows' list — if the code graph evidences no flows, do not "
              "write an empty graph (see references/domain-derivation.md).",
              file=sys.stderr)
        return 1

    ensure_tmp_dir_gitignored(args.repo)
    path = write_flow_graph(args.repo, flow_graph, dest_rel=TMP_REL)
    print(f"Wrote {path} ({len(flow_graph['flows'])} flows, provisional/derived — never committed)")
    print("Re-run precheck_graph.py --need flow to confirm READY.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="command", required=True)

    p_prepare = sub.add_parser("prepare", help="emit a compact code-graph digest for the analyzer")
    p_prepare.add_argument("--repo", required=True, type=Path)
    p_prepare.set_defaults(func=run_prepare)

    p_write = sub.add_parser("write", help="validate the analyzer output and write the derived flow graph")
    p_write.add_argument("--repo", required=True, type=Path)
    p_write.add_argument("--analysis", required=True, type=Path)
    p_write.set_defaults(func=run_write)

    args = ap.parse_args()
    if not args.repo.is_dir():
        print(f"Not a directory: {args.repo}", file=sys.stderr)
        return 2
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
