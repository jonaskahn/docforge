# Adding a graph source

Docforge reads a **code graph** (required) and, where available, a **flow graph** through a small registry of *sources*. Two ship today — Understand-Anything and GitNexus — and adding another (codegraph, graphify, …) touches exactly three things. Nothing in `precheck_graph`, `read_graph`, or any instruction file changes.

## Naming convention

Everything specific to your source carries the `graph_source_<name>` prefix: the scripts `scripts/graph_source_<name>.py`/`.js`, an optional offline reader `scripts/graph_source_<name>_reader.py`/`.js` if it is DB-backed, and the reference `references/graph-source-<name>.md`. Source-agnostic pieces (`graph_source_registry`, `read_graph`, `precheck_graph`, `graph_storage`) never carry a source name. Each source-specific file opens by stating which source and need it serves.

## The `SOURCE` descriptor

Write `scripts/graph_source_<name>.py` and `scripts/graph_source_<name>.js` (both — every docforge script is a dual mirror). Each exposes a `SOURCE` descriptor:

```
SOURCE = {
  "name": "<stable-id>",          # e.g. "codegraph"
  "display": "<Human Label>",
  "capabilities": {"code_graph"}  # and/or "flow_graph" — only what it can actually provide
  "read_mode": "json",            # "json" (read with read_graph) or "db" (native interface)
  "detect": detect,               # (repo) -> {"code_graph": path|None, "flow_graph": path|None, ...}
  "setup_hint": setup_hint,       # (repo, gap) -> [lines] telling the user how to produce a missing graph
}
```

- **`detect(repo)`** returns, for each capability, the path to a graph docforge can read *now* (or `None`). It may add source-private keys (GitNexus adds `index`, `stats`, `stale`). Reuse `graph_storage.find_graph_file(repo, candidates)` — it searches up to the git root so subdirectory invocation works.
- **`read_mode`** tells the orchestrator how the graph is read. There are two shapes, and no build-to-JSON step for either:
  - **`"json"`** — the source writes a JSON graph docforge reads directly (understand-anything). `detect` points at the `.json` file; `read_graph.py` reads it.
  - **`"db"`** — the source keeps its graph in a database docforge reads in place (GitNexus's ladybug `.gitnexus/lbug`). `detect` points at the DB file (or its index marker); reads go through the source's native interface — an MCP, and/or an optional `graph_source_<name>_reader.{py,js}` that opens the DB directly (see `graph_source_gitnexus_reader.py`). Do **not** copy the DB into JSON; read it where it lives.
- **`setup_hint(repo, gap)`** returns the lines `precheck_graph` prints when that capability is missing. `gap` is `"code_graph"` or `"flow_graph"`. Indented command lines (four spaces) are printed as-is; other lines get a two-space prefix.

### Capabilities

- `code_graph` — structure/knowledge graph. Universal precondition. A source that provides only this is fully useful; docforge derives a flow graph from it when needed (`references/domain-derivation.md`).
- `flow_graph` — business-flow/domain graph. Optional. Provide it only if the source genuinely emits flows (both shipping sources do, so derivation is only for a code-graph-only source).

## Register it

Add one import + one list entry, in priority order, to **both** `scripts/graph_source_registry.py` and `scripts/graph_source_registry.js`:

```python
import graph_source_codegraph as codegraph
SOURCES = [understand_anything.SOURCE, gitnexus.SOURCE, codegraph.SOURCE]
```

Earlier entries win when the caller wants a single answer; `resolve_all_ready` still reports every ready source so the user can choose.

## Document it

Write `references/graph-source-<name>.md` (the source-specific binding — what it stores, how to detect, how to read, how to build/refresh), and add one column to the capability table in `references/graph-sources.md`. That is the only instruction-prose change: everything else already speaks in capabilities and resolves through that table.

## Verify

- `python scripts/precheck_graph.py --repo <path> --need code` detects your graph with zero orchestrator edits; the miss path prints your `setup_hint` alongside the others, and a ready one prints your `read_mode`'s mechanism.
- Run the Python and Node forms on the same fixture and diff stdout — they must be byte-identical apart from the runtime's own command name.
- For a `"json"` source, `read_graph` reads your code graph if it lands in `.ua/`; if your source uses a different location, add it to `read_graph`'s `DEFAULT_RELPATHS` (both languages). For a `"db"` source, ship the `graph_source_<name>_reader` (both languages) and confirm its graceful path when the driver is not installed.
