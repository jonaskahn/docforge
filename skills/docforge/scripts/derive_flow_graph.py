#!/usr/bin/env python3
"""Docforge's own flow-graph derivation — build a provisional domain/flow graph
from an existing code graph when no native flow graph is available.

Docforge needs a flow graph for docs/flows/, docs/product/, the BA/PO overlays,
and agent-context flow sections. When a source supplies one natively (an
understand-anything flow graph, or GitNexus's native processes) docforge uses
that. When none exists — a code-graph-only source with no flow data — docforge
derives one *from the code graph it already has*, grounded in the graph and
never invented, and writes it to .docforge/tmp/flow-graph.json: provisional,
git-ignored, regenerated each run, never committed.

The reasoning step is agent-mediated (a script cannot infer business domains):

    python derive_flow_graph.py prepare --repo <path>
    # -> writes .docforge/tmp/domain-context.json (compact code-graph digest)
    # The agent dispatches the docforge domain analyzer on that context per
    # references/flow-derivation.md and saves its JSON to <analysis.json>.
    python derive_flow_graph.py write --repo <path> --analysis <analysis.json>
    # -> validates and writes .docforge/tmp/flow-graph.json (+ .gitignore)

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

# Main-flow budget and traversal radius for the entry-point-first strategy.
DEFAULT_MAX_FLOWS = 15
DEFAULT_HOPS = 3

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


def _slim_nodes(nodes: list) -> tuple[list, dict]:
    """Normalize source nodes to docforge's slim shape and index them by id."""
    slim = []
    by_id = {}
    for node in nodes:
        nid = first_present(node, ID_KEYS)
        record = {
            "id": nid,
            "name": first_present(node, LABEL_KEYS),
            "type": first_present(node, KIND_KEYS),
            "path": first_present(node, PATH_KEYS),
            "summary": first_present(node, SUMMARY_KEYS),
        }
        slim.append(record)
        if nid is not None:
            by_id[str(nid)] = record
    return slim, by_id


def _flow_edges(edges: list) -> list:
    """Keep only edges that carry flow/structure signal, in slim shape."""
    slim = []
    for edge in edges:
        kind = str(first_present(edge, EDGEKIND_KEYS) or "").lower()
        if not any(hint in kind for hint in FLOW_EDGE_HINTS):
            continue
        slim.append({
            "source": first_present(edge, SRC_KEYS),
            "target": first_present(edge, DST_KEYS),
            "type": first_present(edge, EDGEKIND_KEYS),
        })
    return slim


def _bounded_cluster(seed_id, adjacency: dict, by_id: dict, hops: int) -> list:
    """Breadth-first walk from a seed over flow edges, collecting node ids
    reachable within `hops` hops (the seed's flow neighbourhood). Nodes are
    returned in BFS-visit order — deterministic, and identical to the Node
    twin's insertion-ordered Set (do not iterate a Python set here: its order
    is hash-based and would break py/js parity)."""
    seen = {str(seed_id)}
    order = [str(seed_id)]
    frontier = [str(seed_id)]
    for _ in range(max(hops, 0)):
        nxt = []
        for nid in frontier:
            for target in adjacency.get(nid, ()):  # outgoing flow edges only
                if target not in seen:
                    seen.add(target)
                    order.append(target)
                    nxt.append(target)
        frontier = nxt
        if not frontier:
            break
    return [by_id[nid] for nid in order if nid in by_id]


def _entry_point_context(doc, seeds, source, path, repo, max_flows, hops) -> dict:
    """Entry-point-first context: the top `max_flows` seeds, each with its
    bounded flow neighbourhood — dozens of nodes per flow, not the whole graph."""
    slim, by_id = _slim_nodes(locate_collection(doc, NODE_KEYS))
    edges = _flow_edges(locate_collection(doc, EDGE_KEYS))
    adjacency: dict = {}
    for edge in edges:
        src, dst = edge["source"], edge["target"]
        if src is not None and dst is not None:
            adjacency.setdefault(str(src), []).append(str(dst))

    main = seeds[:max_flows]
    clusters = []
    for seed in main:
        cluster_nodes = _bounded_cluster(seed["id"], adjacency, by_id, hops)
        cluster_ids = {str(n["id"]) for n in cluster_nodes}
        cluster_edges = [e for e in edges
                         if str(e["source"]) in cluster_ids and str(e["target"]) in cluster_ids]
        clusters.append({
            "entryPoint": {"id": seed["id"], "name": seed["name"],
                           "kind": seed["kind"], "path": seed["path"]},
            "rank": seed["rank"],
            "nodes": cluster_nodes,
            "edges": cluster_edges,
        })
    return {
        "strategy": "entry-point-first",
        "generatedFrom": str(path),
        "source": source["name"] if source else None,
        "repo": repo.resolve().name,
        "maxFlows": max_flows,
        "hops": hops,
        "entryPointCount": len(seeds),
        "mainFlows": len(main),
        "tail": max(len(seeds) - len(main), 0),
        "clusters": clusters,
    }


def _flat_context(doc, source, path, repo) -> dict:
    """Fallback: the whole flow-signal graph in one dump (pre-entry-point
    behaviour), used only when no entry-point signal is available."""
    slim, _ = _slim_nodes(locate_collection(doc, NODE_KEYS))
    edges = _flow_edges(locate_collection(doc, EDGE_KEYS))
    layers = doc.get("layers") if isinstance(doc.get("layers"), list) else []
    return {
        "strategy": "flat-fallback",
        "generatedFrom": str(path),
        "source": source["name"] if source else None,
        "repo": repo.resolve().name,
        "nodeCount": len(slim),
        "edgeCount": len(edges),
        "nodes": slim,
        "edges": edges,
        "layers": layers,
    }


def _native_interface_context(source, path, repo, read_mode) -> dict:
    """A DB/MCP source whose graph is not a JSON file docforge can load. It is
    never text-loaded here (that is the crash fix) — instead the agent reads it
    through the source's native interface. For CodeGraph (mcp): find entry
    points and codegraph_explore each. For a source with native flows
    (GitNexus): read those directly, do not derive."""
    return {
        "strategy": "mcp-explore" if read_mode == "mcp" else "native-interface",
        "generatedFrom": str(path),
        "source": source["name"] if source else None,
        "repo": repo.resolve().name,
        "readMode": read_mode,
        "instruction": (
            "This source's graph is not a JSON file docforge parses; do NOT dump "
            "the whole graph. Resolve flows entry-point-first through the source's "
            "native interface (references/flow-derivation.md): "
            + ("for CodeGraph, use the codegraph MCP to rank entry points "
               "(route nodes, then exported functions with no incoming call, then "
               "call fan-out) and run codegraph_explore once per main entry point, "
               "documenting the top flows first."
               if read_mode == "mcp" else
               "read the source's native flows/processes directly and rank them "
               "main-first (e.g. GitNexus: cross_community processes, then step "
               "count); do not derive what the source already models.")
        ),
    }


def build_context(repo: Path, max_flows: int, hops: int) -> dict:
    """Resolve the code graph and build the analyzer context, dispatched on the
    source's read_mode. Only a JSON source is ever text-loaded here — a db/mcp
    source is routed to its native interface, so a binary graph never reaches a
    JSON reader (the crash fix)."""
    source, path = resolve_first_ready(repo, "code_graph")
    if not path:
        raise ValueError(
            "no code graph found — derivation needs one to work from. Run "
            "precheck_graph.py --need code for how to build it."
        )
    read_mode = source.get("read_mode") if source else "json"
    entry_fn = source.get("entry_points") if source else None

    if read_mode == "json":
        doc = load_json(path)
        seeds = entry_fn(repo) if entry_fn else []
        if seeds:
            return _entry_point_context(doc, seeds, source, path, repo, max_flows, hops)
        return _flat_context(doc, source, path, repo)

    # db / mcp: binary graph — never load_json it.
    seeds = entry_fn(repo) if entry_fn else []
    if seeds:
        # An offline seed reader is available for this DB source (post the
        # reader decision): fall through to a seed-only manifest.
        return {
            "strategy": "entry-point-first",
            "generatedFrom": str(path),
            "source": source["name"] if source else None,
            "repo": repo.resolve().name,
            "maxFlows": max_flows,
            "hops": hops,
            "entryPointCount": len(seeds),
            "mainFlows": len(seeds[:max_flows]),
            "tail": max(len(seeds) - max_flows, 0),
            "entryPoints": seeds[:max_flows],
            "note": "Seeds read offline; spread each via the source's reader or "
                    "MCP, main flows first (references/flow-derivation.md).",
        }
    return _native_interface_context(source, path, repo, read_mode)


def _report_prepare(context: dict) -> None:
    strategy = context.get("strategy")
    if strategy == "entry-point-first":
        print(f"Strategy: entry-point-first — {context.get('mainFlows')} main flow(s) "
              f"of {context.get('entryPointCount')} entry points "
              f"({context.get('tail')} in the tail), source: {context['source']}")
    elif strategy == "flat-fallback":
        print(f"Strategy: flat-fallback (no entry-point signal) — "
              f"{context.get('nodeCount')} nodes, {context.get('edgeCount')} "
              f"flow-signal edges, source: {context['source']}")
    else:
        print(f"Strategy: {strategy} — read via the source's native interface, "
              f"source: {context['source']} (no graph dumped)")


def run_prepare(args: argparse.Namespace) -> int:
    try:
        context = build_context(args.repo, args.max_flows, args.hops)
    except ValueError as error:
        print(f"PREPARE FAILED: {error}", file=sys.stderr)
        return 1
    ensure_tmp_dir_gitignored(args.repo)
    out = args.repo.resolve() / TMP_REL / CONTEXT_NAME
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(context, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {out}")
    _report_prepare(context)
    print("Next: dispatch the docforge domain analyzer on this context, main flows "
          "first (references/flow-derivation.md), save its JSON, then run:")
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
              "write an empty graph (see references/flow-derivation.md).",
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

    p_prepare = sub.add_parser("prepare", help="emit an entry-point-first code-graph digest for the analyzer")
    p_prepare.add_argument("--repo", required=True, type=Path)
    p_prepare.add_argument("--max-flows", type=int, default=DEFAULT_MAX_FLOWS,
                           help=f"main-flow budget: how many top entry points to expand "
                                f"(default {DEFAULT_MAX_FLOWS}); the rest are the tail")
    p_prepare.add_argument("--hops", type=int, default=DEFAULT_HOPS,
                           help=f"how many call/contains hops to spread from each entry "
                                f"point (default {DEFAULT_HOPS})")
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
