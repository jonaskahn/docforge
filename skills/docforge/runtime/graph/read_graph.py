#!/usr/bin/env python3
"""Read a JSON code graph and extract the inventories that seed a
documentation set.

This reads a **JSON** graph on disk — understand-anything's
.ua/knowledge-graph.json (or the legacy .understand-anything/ path). A
**DB-backed** source (GitNexus's ladybug .gitnexus/lbug) is not a JSON file and
is not read here: query it via the gitnexus MCP, or offline with
scripts/graph_source_gitnexus_reader.py — see references/graph/graph-sources.md for
the read dispatch.

The on-disk schema is not assumed. The script probes the JSON, reports the shape
it found, and extracts only fields it can actually see. Where a field is absent
it says so rather than substituting a guess — the whole point of reading the
graph is to stop inventing.

Typical use:

    python read_graph.py --summary
    python read_graph.py --graph <path/to/knowledge-graph.json> --probe
    python read_graph.py --modules --deps

If --graph is omitted, the graph is located at the repository root by searching
the known JSON store locations (`.ua/`, legacy `.understand-anything/`) up every
parent to the git root, so it works when invoked from a subdirectory.

Standard library only. Output is an inventory to verify, not finished prose.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

DEFAULT_RELPATHS = [
    Path(".ua/knowledge-graph.json"),
    Path(".understand-anything/knowledge-graph.json"),
]


def find_default_graph(start: Path | None = None) -> Path | None:
    """Locate the graph relative to the repo root, not just the CWD.

    The graph lives at the project root ($PROJECT_ROOT/.ua/knowledge-graph.json).
    When invoked from a subdirectory a plain CWD-relative lookup reports "not
    found" even though the file exists at the root, so search the CWD and every
    ancestor up to (and including) the git root or the filesystem root.
    """
    start = (start or Path.cwd()).resolve()
    for base in (start, *start.parents):
        for rel in DEFAULT_RELPATHS:
            candidate = base / rel
            if candidate.is_file():
                return candidate
        if (base / ".git").exists():
            break  # reached the repo root; do not climb past it
    return None

# Candidate key names, in preference order. The pipeline's schema may evolve or
# differ by version, so every lookup is a search rather than an assumption.
NODE_KEYS = ["nodes", "files", "entities", "items"]
EDGE_KEYS = ["edges", "links", "relationships", "relations"]
ID_KEYS = ["id", "nodeId", "key", "name"]
PATH_KEYS = ["path", "filePath", "file", "relativePath", "location"]
LABEL_KEYS = ["name", "label", "title", "symbol"]
KIND_KEYS = ["type", "kind", "nodeType", "category"]
LAYER_KEYS = ["layer", "architecturalLayer", "group", "tier"]
SUMMARY_KEYS = ["summary", "description", "explanation", "doc"]
SRC_KEYS = ["source", "from", "src", "start"]
DST_KEYS = ["target", "to", "dst", "end"]
EDGEKIND_KEYS = ["type", "kind", "relation", "label"]
EXTERNAL_HINTS = ["external", "isExternal", "thirdParty", "builtin"]


def first_present(node: dict, keys: list[str]) -> Any:
    for key in keys:
        if isinstance(node, dict) and key in node and node[key] not in (None, ""):
            return node[key]
    return None


def locate_collection(doc: Any, keys: list[str], depth: int = 3) -> tuple[str, list]:
    """Locate a list of dicts under one of `keys`, searching nested objects."""
    if not isinstance(doc, dict) or depth < 0:
        return "", []
    for key in keys:
        value = doc.get(key)
        if isinstance(value, list) and (not value or isinstance(value[0], dict)):
            return key, value
        if isinstance(value, dict):  # e.g. {"nodes": {"id": {...}}}
            entries = list(value.values())
            if entries and isinstance(entries[0], dict):
                return key, entries
    for key, value in doc.items():
        if isinstance(value, dict):
            path, found = locate_collection(value, keys, depth - 1)
            if found:
                return f"{key}.{path}", found
    return "", []


def load_graph(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        sys.exit(f"No graph at {path}. Build a code graph from any configured "
                 "source first — see references/graph/graph-sources.md.")
    except json.JSONDecodeError as error:
        sys.exit(f"{path} is not valid JSON ({error}). The graph may be mid-write.")
    if not isinstance(data, dict):
        sys.exit(f"Unexpected top-level type in {path}: {type(data).__name__}")
    return data


# ---------------------------------------------------------------------------

def describe_shape(doc: dict, nkey: str, nodes: list, ekey: str, edges: list) -> None:
    print("SHAPE")
    print(f"  top-level keys : {', '.join(sorted(doc)[:20])}")
    print(f"  nodes          : {nkey or '(not found)'} — {len(nodes)}")
    print(f"  edges          : {ekey or '(not found)'} — {len(edges)}")
    if nodes:
        sample = nodes[0]
        print(f"  node fields    : {', '.join(sorted(sample)[:24])}")
        for label, keys in (("id", ID_KEYS), ("path", PATH_KEYS),
                            ("kind", KIND_KEYS), ("layer", LAYER_KEYS),
                            ("summary", SUMMARY_KEYS)):
            value = first_present(sample, keys)
            shown = str(value)[:70] if value is not None else "(absent in sample)"
            print(f"    {label:<8}-> {shown}")
    if edges:
        print(f"  edge fields    : {', '.join(sorted(edges[0])[:24])}")
    if not nodes:
        print("\n  No node collection recognized. Inspect the file directly and\n"
              "  adapt, rather than reporting facts this script did not read.")


def modules(nodes: list, limit: int) -> None:
    counts: dict[str, Counter] = defaultdict(Counter)
    summaries: dict[str, str] = {}
    for node in nodes:
        if any(node.get(h) is True for h in EXTERNAL_HINTS):
            continue
        location = first_present(node, PATH_KEYS) or first_present(node, LABEL_KEYS)
        if not location:
            continue
        parts = str(location).replace("\\", "/").split("/")
        module = "/".join(parts[:-1]) or "."
        counts[module][first_present(node, KIND_KEYS) or "unknown"] += 1
        summary = first_present(node, SUMMARY_KEYS)
        if summary and module not in summaries:
            summaries[module] = " ".join(str(summary).split())[:150]

    print(f"MODULES ({len(counts)})")
    for module, kinds in sorted(counts.items(), key=lambda kv: -sum(kv[1].values()))[:limit]:
        total = sum(kinds.values())
        detail = ", ".join(f"{k}:{v}" for k, v in kinds.most_common(4))
        print(f"  {module}/  [{total}] {detail}")
        if module in summaries:
            print(f"      {summaries[module]}")
    if len(counts) > limit:
        print(f"  ... {len(counts) - limit} more (raise --limit)")
    print("\n  Seeds the code map in docs/architecture/high-level.md. Confirm each\n"
          "  module's purpose with a subsystem deep-dive (references/graph/graph-sources.md,\n"
          "  'Deep-dive a symbol') before describing it.")


def layers(nodes: list) -> None:
    counter = Counter()
    for node in nodes:
        layer_value = first_present(node, LAYER_KEYS)
        if layer_value:
            counter[str(layer_value)] += 1
    if not counter:
        print("LAYERS\n  No layer field found on nodes. Derive grouping from the\n"
              "  module inventory instead, or rebuild the code graph "
              "(references/graph/graph-sources.md).")
        return
    print(f"LAYERS ({len(counter)})")
    for layer, count in counter.most_common():
        print(f"  {layer:<24} {count}")


def deps(nodes: list, edges: list, limit: int) -> None:
    known = set()
    for node in nodes:
        for key in ID_KEYS + PATH_KEYS:
            value = node.get(key) if isinstance(node, dict) else None
            if value:
                known.add(str(value))

    external = Counter()
    for node in nodes:
        if any(node.get(h) is True for h in EXTERNAL_HINTS):
            name = first_present(node, LABEL_KEYS) or first_present(node, PATH_KEYS)
            if name:
                external[str(name)] += 1

    for edge in edges:
        kind = str(first_present(edge, EDGEKIND_KEYS) or "").lower()
        if "import" not in kind and "depend" not in kind and "require" not in kind:
            continue
        target = first_present(edge, DST_KEYS)
        if target is None:
            continue
        text = str(target)
        if text in known or text.startswith((".", "/", "src", "app", "lib", "pkg")):
            continue
        external[text.split("/")[0] if not text.startswith("@") else "/".join(text.split("/")[:2])] += 1

    if not external:
        print("EXTERNAL REFERENCES\n  None distinguishable from this graph. Take the\n"
              "  inventory from the manifest and lockfile instead.")
        return
    print(f"EXTERNAL REFERENCES ({len(external)})")
    for name, count in external.most_common(limit):
        print(f"  {name:<40} {count} reference(s)")
    print("\n  Candidates for docs/architecture/dependencies.md. Versions and\n"
          "  licences come from the manifest; criticality and failure behaviour\n"
          "  come from the team or a targeted graph query (references/graph/graph-sources.md).")


def boundaries(nodes: list, edges: list) -> None:
    """Report which top-level modules do and do not reach each other.

    Absent edges are how architectural invariants are evidenced.
    """
    roots = {"src", "app", "lib", "pkg", "internal", "packages", "source"}

    def top(value: Any) -> str:
        """First meaningful path segment, skipping a conventional source root."""
        if not value:
            return ""
        parts = [segment for segment in str(value).replace("\\", "/").split("/") if segment]
        if parts and parts[0] in roots and len(parts) > 1:
            parts = parts[1:]
        return parts[0] if parts else ""

    index = {}
    for node in nodes:
        node_id = first_present(node, ID_KEYS)
        if node_id is not None:
            index[str(node_id)] = top(first_present(node, PATH_KEYS) or first_present(node, LABEL_KEYS))

    pairs: Counter = Counter()
    for edge in edges:
        source, target = first_present(edge, SRC_KEYS), first_present(edge, DST_KEYS)
        if str(source) not in index or str(target) not in index:
            continue  # unresolved endpoint — usually external, not a boundary
        a, b = index[str(source)], index[str(target)]
        if a and b and a != b:
            pairs[(a, b)] += 1

    if not pairs:
        print("BOUNDARIES\n  No cross-module edges resolved. Check --probe output.")
        return
    mods = sorted({m for pair in pairs for m in pair})
    print(f"CROSS-MODULE EDGES ({len(pairs)} directed pairs over {len(mods)} modules)")
    for (a, b), count in pairs.most_common(30):
        print(f"  {a} -> {b}   {count}")
    absent = [(a, b) for a in mods for b in mods
              if a != b and (a, b) not in pairs and (b, a) in pairs]
    if absent:
        print("\n  One-directional (candidate invariants — confirm intent before asserting):")
        for a, b in absent[:15]:
            print(f"    nothing in {a} reaches {b}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--graph", type=Path, help="path to knowledge-graph.json")
    ap.add_argument("--probe", action="store_true", help="report the file's shape only")
    ap.add_argument("--summary", action="store_true", help="probe + modules + layers + deps")
    ap.add_argument("--modules", action="store_true")
    ap.add_argument("--layers", action="store_true")
    ap.add_argument("--deps", action="store_true")
    ap.add_argument("--boundaries", action="store_true",
                    help="cross-module edges and one-directional pairs")
    ap.add_argument("--limit", type=int, default=40)
    args = ap.parse_args()

    path = args.graph
    if path is None:
        path = find_default_graph()
        if path is None:
            sys.exit("No JSON code graph found in $PROJECT_ROOT/.ua/ or "
                     "$PROJECT_ROOT/.understand-anything/ (searched the current "
                     "directory and every parent up to the repo root). If the "
                     "active source is GitNexus, its graph is a ladybug DB — read "
                     "it via the gitnexus MCP or scripts/graph_source_gitnexus_reader.py "
                     "(references/graph/graph-sources.md), not this script. Otherwise "
                     "build a JSON code graph, or pass --graph <path> explicitly.")

    doc = load_graph(path)
    nkey, nodes = locate_collection(doc, NODE_KEYS)
    ekey, edges = locate_collection(doc, EDGE_KEYS)

    print(f"# {path}  ({path.stat().st_size / 1024:.0f} KB)\n")

    want_all = args.summary or not any(
        (args.probe, args.modules, args.layers, args.deps, args.boundaries))
    if args.probe or want_all:
        describe_shape(doc, nkey, nodes, ekey, edges)
        print()
    if not nodes:
        return 1
    if args.modules or want_all:
        modules(nodes, args.limit); print()
    if args.layers or want_all:
        layers(nodes); print()
    if args.deps or want_all:
        deps(nodes, edges, args.limit); print()
    if args.boundaries:
        boundaries(nodes, edges); print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
