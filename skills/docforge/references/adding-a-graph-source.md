# Adding a graph source

Docforge reads a **code graph** (required) and, where available, a **flow graph** through a small registry of *sources*. Three ship today — Understand-Anything, GitNexus, and CodeGraph — and adding another (graphify, …) touches exactly three things. Nothing in `precheck_graph`, `read_graph`, or any instruction file changes.

## Naming convention

Everything specific to your source carries the `graph_source_<name>` prefix: the scripts `scripts/graph_source_<name>.py`/`.js`, an optional offline reader `scripts/graph_source_<name>_reader.py`/`.js` if it is DB-backed, and the reference `references/graph-source-<name>.md`. Source-agnostic pieces (`graph_source_registry`, `read_graph`, `precheck_graph`, `graph_storage`) never carry a source name. Each source-specific file opens by stating which source and need it serves.

## The `SOURCE` descriptor

Write `scripts/graph_source_<name>.py` and `scripts/graph_source_<name>.js` (both — every docforge script is a dual mirror). Each exposes a `SOURCE` descriptor:

```
SOURCE = {
  "name": "<stable-id>",          # e.g. "graphify"
  "display": "<Human Label>",
  "capabilities": {"code_graph"}  # and/or "flow_graph" — only what it can actually provide
  "read_mode": "json",            # "json" (read with read_graph), "db" (native interface,
                                   #   optional offline reader), or "mcp" (native interface
                                   #   only — no offline reader, e.g. CodeGraph)
  "detect": detect,               # (repo) -> {"code_graph": path|None, "flow_graph": path|None, ...}
  "setup_hint": setup_hint,       # (repo, gap) -> [lines] telling the user how to produce a missing graph
}
```

- **`detect(repo)`** returns, for each capability, the path to a graph docforge can read *now* (or `None`). It may add source-private keys (GitNexus adds `index`, `stats`, `stale`). Reuse `graph_storage.find_graph_file(repo, candidates)` — it searches up to the git root so subdirectory invocation works.
- **`read_mode`** tells the orchestrator how the graph is read. There are three shapes, and no build-to-JSON step for any of them:
  - **`"json"`** — the source writes a JSON graph docforge reads directly (understand-anything). `detect` points at the `.json` file; `read_graph.py` reads it.
  - **`"db"`** — the source keeps its graph in a database docforge reads in place (GitNexus's ladybug `.gitnexus/lbug`). `detect` points at the DB file (or its index marker); reads go through the source's native interface — an MCP, and/or an optional `graph_source_<name>_reader.{py,js}` that opens the DB directly (see `graph_source_gitnexus_reader.py`). Do **not** copy the DB into JSON; read it where it lives.
  - **`"mcp"`** — same as `"db"`, but there is no offline reader at all and none is planned (CodeGraph's SQLite `.codegraph/codegraph.db`, read only through `codegraph_explore`). `detect` still only checks the file's presence on disk — it cannot confirm the MCP tool is wired into the calling agent's session, since that's invisible to a subprocess. `setup_hint` and the reference doc must say so explicitly: a `"mcp"` source's on-disk readiness does not guarantee it is actually readable this session.
- **`setup_hint(repo, gap)`** returns the lines `precheck_graph` prints when that capability is missing. `gap` is `"code_graph"` or `"flow_graph"`. Indented command lines (four spaces) are printed as-is; other lines get a two-space prefix.
- **`entry_points(repo)`** *(optional)* returns ranked flow-derivation seeds — `[{"id", "name", "kind", "path", "rank"}]`, highest `rank` first — read from your source's own entry-point signal (framework routes, exported-but-uncalled functions, entry-point tags…), **never a full scan**. `derive_flow_graph` uses it to build an entry-point-first, main-flow-first context instead of dumping the whole graph. Omit it and a `json` source falls back to the flat dump; a `db`/`mcp` source without it routes to its native interface (`mcp-explore` / `native-interface`). Provide it when your source carries cheap entry-point signal — it is what makes flow derivation focused rather than a soup. See `references/flow-derivation.md`.

### Capabilities

- `code_graph` — structure and call/import relationships. Universal precondition. A source that provides only this is fully useful; docforge derives a flow graph from it when needed (`references/flow-derivation.md`).
- `flow_graph` — business flows and ordered steps. Optional. Provide it only if the source genuinely emits flows (understand-anything and GitNexus both do; CodeGraph doesn't, so derivation covers flow docs when it is the only ready source).

## Register it

Add one import + one list entry, in priority order, to **both** `scripts/graph_source_registry.py` and `scripts/graph_source_registry.js`:

```python
import graph_source_graphify as graphify
SOURCES = [understand_anything.SOURCE, gitnexus.SOURCE, codegraph.SOURCE, graphify.SOURCE]
```

Earlier entries win when the caller wants a single answer; `resolve_all_ready` still reports every ready source so the user can choose.

## Document it

Write `references/graph-source-<name>.md` (the source-specific binding — what it stores, how to detect, how to read, how to build/refresh), and add one column to the capability table in `references/graph-sources.md`. That is the only instruction-prose change: everything else already speaks in capabilities and resolves through that table.

## Verify

- `python scripts/precheck_graph.py --repo <path> --need code` detects your graph with zero orchestrator edits; the miss path prints your `setup_hint` alongside the others, and a ready one prints your `read_mode`'s mechanism.
- Run the Python and Node forms on the same fixture and diff stdout — they must be byte-identical apart from the runtime's own command name.
- For a `"json"` source, `read_graph` reads your code graph if it lands in `.ua/`; if your source uses a different location, add it to `read_graph`'s `DEFAULT_RELPATHS` (both languages). For a `"db"` source, ship the `graph_source_<name>_reader` (both languages) and confirm its graceful path when the driver is not installed. For an `"mcp"` source (no reader at all, like CodeGraph), confirm the reference doc states the two-gate check explicitly — on-disk presence alone must never be presented to the agent as "readable."
