#!/usr/bin/env python3
"""Read a knowledge graph produced by the understand-anything pipeline and
extract the inventories that seed a documentation set.

The on-disk schema is not assumed. The script probes the JSON, reports the shape
it found, and extracts only fields it can actually see. Where a field is absent
it says so rather than substituting a guess — the whole point of reading the
graph is to stop inventing.

Typical use:

    python graph_extract.py --graph .ua/knowledge-graph.json --summary
    python graph_extract.py --graph .ua/knowledge-graph.json --probe
    python graph_extract.py --graph .ua/knowledge-graph.json --modules --deps

If --graph is omitted, the graph is located at the repository root —
$PROJECT_ROOT/.ua/knowledge-graph.json then $PROJECT_ROOT/.understand-anything/knowledge-graph.json —
by searching the current directory and every parent up to the git root, so it
works when invoked from a subdirectory.

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


def first(d: dict, keys: list[str]) -> Any:
    for k in keys:
        if isinstance(d, dict) and k in d and d[k] not in (None, ""):
            return d[k]
    return None


def find_collection(doc: Any, keys: list[str], depth: int = 3) -> tuple[str, list]:
    """Locate a list of dicts under one of `keys`, searching nested objects."""
    if not isinstance(doc, dict) or depth < 0:
        return "", []
    for k in keys:
        v = doc.get(k)
        if isinstance(v, list) and (not v or isinstance(v[0], dict)):
            return k, v
        if isinstance(v, dict):  # e.g. {"nodes": {"id": {...}}}
            vals = list(v.values())
            if vals and isinstance(vals[0], dict):
                return k, vals
    for k, v in doc.items():
        if isinstance(v, dict):
            path, found = find_collection(v, keys, depth - 1)
            if found:
                return f"{k}.{path}", found
    return "", []


def load(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        sys.exit(f"No graph at {path}. Build one with /understand first.")
    except json.JSONDecodeError as e:
        sys.exit(f"{path} is not valid JSON ({e}). The graph may be mid-write.")
    if not isinstance(data, dict):
        sys.exit(f"Unexpected top-level type in {path}: {type(data).__name__}")
    return data


# ---------------------------------------------------------------------------

def probe(doc: dict, nkey: str, nodes: list, ekey: str, edges: list) -> None:
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
            v = first(sample, keys)
            shown = str(v)[:70] if v is not None else "(absent in sample)"
            print(f"    {label:<8}-> {shown}")
    if edges:
        print(f"  edge fields    : {', '.join(sorted(edges[0])[:24])}")
    if not nodes:
        print("\n  No node collection recognized. Inspect the file directly and\n"
              "  adapt, rather than reporting facts this script did not read.")


def modules(nodes: list, limit: int) -> None:
    counts: dict[str, Counter] = defaultdict(Counter)
    summaries: dict[str, str] = {}
    for n in nodes:
        if any(n.get(h) is True for h in EXTERNAL_HINTS):
            continue
        p = first(n, PATH_KEYS) or first(n, LABEL_KEYS)
        if not p:
            continue
        parts = str(p).replace("\\", "/").split("/")
        mod = "/".join(parts[:-1]) or "."
        counts[mod][first(n, KIND_KEYS) or "unknown"] += 1
        s = first(n, SUMMARY_KEYS)
        if s and mod not in summaries:
            summaries[mod] = " ".join(str(s).split())[:150]

    print(f"MODULES ({len(counts)})")
    for mod, kinds in sorted(counts.items(), key=lambda kv: -sum(kv[1].values()))[:limit]:
        total = sum(kinds.values())
        detail = ", ".join(f"{k}:{v}" for k, v in kinds.most_common(4))
        print(f"  {mod}/  [{total}] {detail}")
        if mod in summaries:
            print(f"      {summaries[mod]}")
    if len(counts) > limit:
        print(f"  ... {len(counts) - limit} more (raise --limit)")
    print("\n  Seeds the code map in docs/architecture/high-level.md. Confirm each\n"
          "  module's purpose with /understand-explain before describing it.")


def layers(nodes: list) -> None:
    c = Counter()
    for n in nodes:
        lv = first(n, LAYER_KEYS)
        if lv:
            c[str(lv)] += 1
    if not c:
        print("LAYERS\n  No layer field found on nodes. Derive grouping from the\n"
              "  module inventory instead, or re-run /understand.")
        return
    print(f"LAYERS ({len(c)})")
    for layer, n in c.most_common():
        print(f"  {layer:<24} {n}")


def deps(nodes: list, edges: list, limit: int) -> None:
    known = set()
    for n in nodes:
        for k in ID_KEYS + PATH_KEYS:
            v = n.get(k) if isinstance(n, dict) else None
            if v:
                known.add(str(v))

    external = Counter()
    for n in nodes:
        if any(n.get(h) is True for h in EXTERNAL_HINTS):
            name = first(n, LABEL_KEYS) or first(n, PATH_KEYS)
            if name:
                external[str(name)] += 1

    for e in edges:
        kind = str(first(e, EDGEKIND_KEYS) or "").lower()
        if "import" not in kind and "depend" not in kind and "require" not in kind:
            continue
        tgt = first(e, DST_KEYS)
        if tgt is None:
            continue
        t = str(tgt)
        if t in known or t.startswith((".", "/", "src", "app", "lib", "pkg")):
            continue
        external[t.split("/")[0] if not t.startswith("@") else "/".join(t.split("/")[:2])] += 1

    if not external:
        print("EXTERNAL REFERENCES\n  None distinguishable from this graph. Take the\n"
              "  inventory from the manifest and lockfile instead.")
        return
    print(f"EXTERNAL REFERENCES ({len(external)})")
    for name, n in external.most_common(limit):
        print(f"  {name:<40} {n} reference(s)")
    print("\n  Candidates for docs/architecture/dependencies.md. Versions and\n"
          "  licences come from the manifest; criticality and failure behaviour\n"
          "  come from the team or from /understand-chat.")


def boundaries(nodes: list, edges: list) -> None:
    """Report which top-level modules do and do not reach each other.

    Absent edges are how architectural invariants are evidenced.
    """
    roots = {"src", "app", "lib", "pkg", "internal", "packages", "source"}

    def top(v: Any) -> str:
        """First meaningful path segment, skipping a conventional source root."""
        if not v:
            return ""
        parts = [q for q in str(v).replace("\\", "/").split("/") if q]
        if parts and parts[0] in roots and len(parts) > 1:
            parts = parts[1:]
        return parts[0] if parts else ""

    idx = {}
    for n in nodes:
        nid = first(n, ID_KEYS)
        if nid is not None:
            idx[str(nid)] = top(first(n, PATH_KEYS) or first(n, LABEL_KEYS))

    pairs: Counter = Counter()
    for e in edges:
        s, t = first(e, SRC_KEYS), first(e, DST_KEYS)
        if str(s) not in idx or str(t) not in idx:
            continue  # unresolved endpoint — usually external, not a boundary
        a, b = idx[str(s)], idx[str(t)]
        if a and b and a != b:
            pairs[(a, b)] += 1

    if not pairs:
        print("BOUNDARIES\n  No cross-module edges resolved. Check --probe output.")
        return
    mods = sorted({m for pair in pairs for m in pair})
    print(f"CROSS-MODULE EDGES ({len(pairs)} directed pairs over {len(mods)} modules)")
    for (a, b), n in pairs.most_common(30):
        print(f"  {a} -> {b}   {n}")
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
            sys.exit("No graph found in $PROJECT_ROOT/.ua/ or $PROJECT_ROOT/.understand-anything/ "
                     "(searched the current directory and every parent up to the "
                     "repo root). Build one with /understand first, or pass "
                     "--graph <path> explicitly.")

    doc = load(path)
    nkey, nodes = find_collection(doc, NODE_KEYS)
    ekey, edges = find_collection(doc, EDGE_KEYS)

    print(f"# {path}  ({path.stat().st_size / 1024:.0f} KB)\n")

    want_all = args.summary or not any(
        (args.probe, args.modules, args.layers, args.deps, args.boundaries))
    if args.probe or want_all:
        probe(doc, nkey, nodes, ekey, edges)
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
