# Graph sources — capability dispatch

Docforge is **provider-agnostic**: it does not care which tool produced the graph it reads. Every graph producer is a *source* registered in `scripts/graph_source_registry.py`/`.js`; three ship today (Understand-Anything, GitNexus, and CodeGraph) and more can be added (see `references/adding-a-graph-source.md`). This file is the single place that maps "I need capability X" to "run this, for whichever source is active." Instruction prose everywhere else names **capabilities**, never a specific command — resolve the command here.

**Naming convention.** Anything specific to one source carries a `graph_source_<name>` (script) / `graph-source-<name>` (reference) **prefix** — `graph_source_gitnexus.py`, `references/graph-source-gitnexus.md`. Source-agnostic pieces carry no marker (`graph_source_registry`, `read_graph`, `precheck_graph`). Adding a source is prefix-in, one registry line, one column here (`references/adding-a-graph-source.md`).

## The requirement model

- **Code graph** (structure / modules / layers / call + import edges) is docforge's **universal precondition**. *Any one* registered source that has built one satisfies it. Docforge never fabricates a code graph itself — if none exists, it stops and tells the user which source to build one with. Check: `python scripts/precheck_graph.py --repo <path> --need code`.
- **Flow graph** (business domains / flows / ordered steps) is needed only for `docs/flows/`, `docs/product/`, the BA/PO overlays, and agent-context flow sections. It is resolved **native-first, else derived**: use a source's flow graph if one exists (understand-anything's domain graph, or GitNexus's native processes); otherwise docforge derives a *provisional* one from the code graph into `.docforge/tmp/domain-graph.json` (never committed — see `references/domain-derivation.md`). So flow docs are never hard-blocked while a code graph exists. Check: `python scripts/precheck_graph.py --repo <path> --need flow`.

## Where the graph lives, and how it is read

There is no single hardcoded store. Each source declares its own location and **read mode**; `precheck_graph` and the readers resolve through the registry, in registry (priority) order:

| Source | Store | Read mode | Code graph | Flow graph |
|---|---|---|---|---|
| Understand-Anything | `.ua/` (legacy `.understand-anything/`) | **JSON** — read with `read_graph.py` | `knowledge-graph.json` | `domain-graph.json` |
| GitNexus | `.gitnexus/lbug` (+ `meta.json`) | **DB** — gitnexus MCP, or `graph_source_gitnexus_reader.py` | the lbug DB (`File`/`Function`/… nodes) | the same DB (native `Process` nodes) |
| CodeGraph | `.codegraph/codegraph.db` | **MCP** — `codegraph_explore` tool only, no offline reader | the SQLite DB (symbols, call/import edges) | — (no flow_graph capability) |
| docforge-derived (provisional) | `.docforge/tmp/domain-graph.json` (git-ignored) | JSON | — | derived from the code graph |

A **JSON** source is read offline with `read_graph.py`; a **DB** source is queried via its native interface (for GitNexus: the MCP, or the offline `graph_source_gitnexus_reader.py`) — never through `read_graph.py`, which is JSON-only. An **MCP** source (CodeGraph) has no offline path at all: `codegraph_explore` or nothing — a present db on disk does not by itself mean the tool is wired into the calling agent's session; confirm the tool is in this session's tool list before treating it as readable (`references/graph-source-codegraph.md`). `precheck_graph` prints the read mechanism next to each ready source.

## Capability → source dispatch

**Priority order, always:** if the capability is already satisfied on disk, use it — it does not matter which source produced it. Only consult "how do I get it" when it is genuinely missing. When more than one source is ready for the same repo, `precheck_graph` reports all of them; ask the user which to read (understand-anything recommended — see `SKILL.md` Step 0).

| Capability | Understand-Anything | GitNexus | CodeGraph | Adding a source |
|---|---|---|---|---|
| Build the code graph | `/understand` | `npx gitnexus analyze` (+ `npx gitnexus setup` once) — `references/graph-source-gitnexus.md` | `codegraph install` (once) + `codegraph init` — user runs both outside the agent, then restarts (`references/graph-source-codegraph.md`) | your `graph_source_<name>` detect/build |
| Refresh after code changes | `/understand` (incremental) or `/understand --auto-update` | `npx gitnexus analyze` (re-index; `detect` flags STALE) | nothing — file-watcher auto-sync keeps the index current | per source |
| Build the flow graph | `/understand-domain` | already native (Process nodes) — nothing to build | not supported — no flow_graph capability | if none available, docforge **derives** one — `references/domain-derivation.md` |
| Read the graph's structure | `read_graph.py --summary` (JSON) | gitnexus MCP `cypher`/`query`, or `graph_source_gitnexus_reader.py --summary` | `codegraph_explore` MCP tool (no offline path) | JSON → `read_graph`; DB → its native reader |
| Scope analysis to a subdirectory | `/understand src/frontend` | not supported (GitNexus always indexes the whole repo) | not supported (indexes the whole repo) | per source |
| Stricter graph validation | `/understand --review` | none | none | per source |
| Deep-dive a symbol (L2/L3 depth) | `/understand-explain <path>` | `context` MCP tool (360° symbol view) | `codegraph_explore` (name the symbol in the query — verbatim source + call paths) | `references/depth-and-audience.md` documents the L0–L3 ladder |
| Enumerate business flows | `/understand-domain` | `query` + `gitnexus://repo/{name}/processes` resource, or `graph_source_gitnexus_reader.py --flows` | not supported — no flow_graph capability | derived flow graph |
| Trace an execution flow | `/understand-explain` + graph query | `gitnexus://repo/{name}/process/{name}` resource | not supported — no flow_graph capability | per source |
| Functional-area / domain grouping | graph layers | `gitnexus://repo/{name}/clusters` (Community nodes, `MEMBER_OF`) | none | per source |
| Blast radius / change impact | inferred from graph edges | `impact` MCP tool | included in `codegraph_explore`'s response (blast-radius summary) | read edges from the code graph directly |
| Diff a PR / working-tree change | `/understand-diff` | `detect_changes` MCP tool | none | per source |
| Visual exploration | `/understand-dashboard` | none | none | per source |
| Onboarding guide generation | `/understand-onboard` | none | none | per source |

**Command name varies by agent.** `/understand` is a skill invocation, not universally a slash command — Codex uses `$understand`, some agents take plain language ("use the understand skill"). GitNexus tools are MCP tools (`query`, `context`, `cypher`, …) and resource reads (`gitnexus://…`); its offline counterpart is `graph_source_gitnexus_reader.{py,js}`. CodeGraph is a single MCP tool, `codegraph_explore`, with no offline counterpart at all — a present `.codegraph/codegraph.db` does not mean the tool is wired into this session; see `references/graph-source-codegraph.md`.

## Adding a source

The whole extension surface is: a `graph_source_<name>.py`/`.js` exposing a `SOURCE` descriptor (with a `read_mode`), one line in `scripts/graph_source_registry.py`/`.js`'s `SOURCES` list, and one column here. Nothing in `precheck_graph` or `read_graph` changes. Full recipe: `references/adding-a-graph-source.md`.
