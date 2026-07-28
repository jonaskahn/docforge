# Deriving a flow graph from the code graph

Docforge needs a **flow graph** — business domains, flows, and ordered steps — for `docs/flows/`, `docs/product/`, the BA/PO overlays, and agent-context flow sections. When a source supplies one natively, use that; it is authoritative. **Two of the three shipping sources do:** Understand-Anything writes a domain graph (`/understand-domain`), and GitNexus carries native `Process` nodes (read them directly — see "When the code graph came from GitNexus" below, and `references/graph-source-gitnexus.md`). So when either of those is the active source, **derivation is never needed** — read the native flows.

Derivation exists for the remaining case: a source that provides **only a code graph, with no native flow data** — CodeGraph is one (it has no flow_graph capability at all), and so would any future code-graph-only source. There, docforge derives one *from the code graph it already has*. The result is **provisional**: written to `.docforge/tmp/domain-graph.json`, git-ignored, regenerated each run, **never committed**. It unblocks flow docs without depending on any one plugin, and it is grounded in the graph — never invented.

> This is docforge's own derivation. It borrows nothing but the general idea (extract domains/flows/steps from an existing graph) — the prompt and output shape below are docforge's.

## Entry-point-first, main-flows-first — not a full-graph dump

The failure mode to avoid: dumping every node and edge at the analyzer and asking it to find the flows in the soup. On a real repo (thousands of nodes) that is slow, unfocused, and blind to *where the application actually starts*. Docforge instead resolves flows the way a person would — **find the entry points, rank them, walk outward from the important ones, and document the main flows before the long tail.**

`derive_flow_graph.py prepare` picks a **strategy** automatically from the active source's `read_mode` and whether it exposes entry-point signal, and stamps it on `.docforge/tmp/domain-context.json` as `strategy`:

| `strategy` | When | What the context holds |
|---|---|---|
| **`entry-point-first`** | The source exposes ranked entry-point seeds (Understand-Anything today; any source with an `entry_points` hook) | The top `--max-flows` seeds, each with its **bounded** flow neighbourhood (`--hops` of `calls`/`contains`/`triggers` edges) as a `clusters` list — dozens of nodes per flow, not the whole graph. `tail` counts the seeds held back. |
| **`mcp-explore`** | The source is MCP-only (CodeGraph) — no offline graph to load | An `instruction`, no node dump: use the codegraph MCP to rank entry points and `codegraph_explore` **once per main entry point**. |
| **`native-interface`** | A DB source with native flows already (GitNexus) reached derivation | An `instruction` to read the source's native flows/processes directly — do not derive what it already models. |
| **`flat-fallback`** | No entry-point signal resolves (non-code repo, or a graph with no routes/exports/tags) | The whole flow-signal graph in one dump — the pre-entry-point behaviour, kept **only** as the last resort. |

**How each source finds its entry points** (the `entry_points` hook, ranked highest-first — `references/graph-sources.md`):

| Source | Entry-point signal (ranked) | Read path |
|---|---|---|
| **Understand-Anything** | `api-handler` tag → `service`/`pipeline` node type → `entry-point` tag (minus `barrel`/`re-export` shims) → `step` type; each boosted by Service/business-layer membership and outgoing-edge fan-out | reads `.ua/knowledge-graph.json` directly (`graph_source_understand_anything.entry_points`) |
| **CodeGraph** | `route` nodes (framework URL surface) → exported functions/methods with **no incoming `calls` edge** (public surface) → `calls` fan-out (hubs) | via the codegraph MCP (the `mcp-explore` strategy) — no offline reader ships today |
| **GitNexus** | native `Process` nodes ranked `cross_community` → step-count → community size | native flows — read, don't derive (`native-interface`) |

The ranking is graph-derived, no configuration. `--max-flows` (default 15) caps how many entry points become "main" flows; `--hops` (default 3) sets how far each flow spreads. When a source exposes no `entry_points` hook and its graph is JSON, `prepare` falls back to the flat dump — nothing breaks, it is just unfocused, and the strategy field says so.

> **Crash-safety.** `prepare` only ever text-loads a `json` source. A `db`/`mcp` source's graph (GitNexus's binary `.gitnexus/lbug`, CodeGraph's SQLite `.codegraph/codegraph.db`) is **never** handed to the JSON reader — it is routed to `mcp-explore`/`native-interface` instead. This is why a CodeGraph-only repo no longer crashes derivation.

## When to run it

`precheck_graph.py --need flow` tells you: `READY` (native or already-derived) → proceed; `MISSING flow graph` while the code graph is present → derive it with the loop below. If the code graph itself is missing, stop — derivation has nothing to work from.

## The loop (agent-mediated)

A script cannot infer business domains, so the reasoning step is a subagent:

1. **Prepare the context.**
   ```
   python scripts/derive_flow_graph.py prepare --repo <path> --max-flows 15 --hops 3
   ```
   Resolves the code graph through the registry, picks the strategy (above), and writes `.docforge/tmp/domain-context.json`. It also drops `.docforge/tmp/.gitignore` so nothing here is committed. Read the `strategy` field and work accordingly:
   - **`entry-point-first`** — work the `clusters` **in order** (they are ranked; the first is the most central flow). Each cluster is one candidate flow with its bounded neighbourhood.
   - **`mcp-explore`** — follow the `instruction`: rank entry points via the codegraph MCP, then `codegraph_explore` each main one; treat each explore result as one flow's evidence.
   - **`native-interface`** — do not derive; read the source's native flows (see "When the code graph came from GitNexus").
   - **`flat-fallback`** — the whole graph is in `nodes`/`edges`; find flows in it as before, but prefer to scope the repo (`/understand <subdir>`, or `--max-flows` once signal exists) rather than lean on this.

2. **Dispatch the docforge domain analyzer** (below) on that context, **main flows first**. Save its JSON to a file, e.g. `.docforge/tmp/analysis.json`.

3. **Write the flow graph.**
   ```
   python scripts/derive_flow_graph.py write --repo <path> --analysis .docforge/tmp/analysis.json
   ```
   Validates the analyzer output against docforge's flow shape and writes `.docforge/tmp/domain-graph.json`. It refuses an empty `flows` list — if the code graph evidences no flows, that is the honest answer; do not write an invented graph.

4. Re-run `precheck_graph.py --need flow` — it now reports the derived (provisional) flow graph. Docs built from it must note flows are provisional and confirm business rules against source before asserting them.

## The docforge domain analyzer (prompt)

Give the subagent the `domain-context.json` and this instruction:

> You extract business structure from a code graph. The context is organized **entry-point-first**: work the ranked `clusters` (or explored entry points) in order — the first flows are the main ones, document them first. Using **only** what the provided graph evidences — nodes, their paths and summaries, and the edges between them — identify the business domains, the flows within them, and each flow's ordered steps. Do not invent a flow, domain, or step that the graph does not support; fewer, well-grounded flows beat a plausible-sounding set. Prefer the code's own business terminology from node names and summaries.
>
> Produce JSON in this shape and nothing else:
> ```json
> {
>   "flows": [
>     {
>       "name": "<flow name>",
>       "domain": "<optional grouping>",
>       "entryPoint": "<optional trigger, e.g. POST /api/orders>",
>       "steps": [ { "order": 1, "name": "<step>", "path": "<file, if known>" } ]
>     }
>   ]
> }
> ```
> Rules: every flow has a non-empty `name` and a `steps` list; steps are ordered by `order` starting at 1; omit `path` when you cannot tie a step to a file rather than guessing; a flow whose steps you cannot order is still valid as a single step; set `entryPoint` from the cluster's entry point where the context provides one. Return the JSON only.

The `write` subcommand stamps `derived: true`, the `source`, `generatedFrom`, and `generatedAt` — the analyzer supplies only `flows` (and optional `domains`).

## When the code graph came from GitNexus

GitNexus already models execution flows natively, so **read them directly — do not derive.** These processes *are* the flow graph; the derivation loop above is only for a source that carries no such data. GitNexus reaches derivation only in the odd case of an index with nodes but no processes, where `prepare` emits the `native-interface` strategy (an instruction, never a crash).

The same **main-flows-first** rule applies when reading them: GitNexus can carry many processes (100+ on a real repo), so rank before documenting — do not read all of them blindly:

- **Rank main flows** — `cross_community` processes span domains and are the primary flows; then by step count, then community size. Document the top ones first; the rest are the long tail.
- **Flows + ordered steps** — the `query({query, goal})` MCP tool returns processes (execution flows) with symbols grouped by flow and file locations; the `gitnexus://repo/{name}/processes` resource lists all flows and `gitnexus://repo/{name}/process/{name}` gives the step-by-step trace. Step order is the 1-indexed `step` field on the `STEP_IN_PROCESS` edge (Cypher: `MATCH (s)-[r:CodeRelation {type:'STEP_IN_PROCESS'}]->(p:Process) WHERE p.heuristicLabel = "<flow>" RETURN s.name, r.step ORDER BY r.step`). Offline (no MCP): `graph_source_gitnexus_reader.py --flows`.
- **Domain grouping** — `gitnexus://repo/{name}/clusters` (Leiden `Community` nodes; membership via `MEMBER_OF`). Each `Process` also carries a `communities[]` property and a `processType` of `intra_community` / `cross_community`, so a flow can be mapped to the domain(s) it spans.
- **Caveat** — GitNexus process labels are code-derived (`Entry → Terminal`), not business phrases. Keep them faithful by default; only rename to business language where a node summary clearly supports it, and note it.

Full GitNexus read recipes are in `references/graph-source-gitnexus.md`.
