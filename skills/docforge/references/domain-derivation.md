# Deriving a flow graph from the code graph

Docforge needs a **flow graph** — business domains, flows, and ordered steps — for `docs/flows/`, `docs/product/`, the BA/PO overlays, and agent-context flow sections. When a source supplies one natively, use that; it is authoritative. **Both shipping sources do:** Understand-Anything writes a domain graph (`/understand-domain`), and GitNexus carries native `Process` nodes (read them directly — see "When the code graph came from GitNexus" below, and `references/graph-source-gitnexus.md`). So on the two sources that ship today, **derivation is never needed** — read the native flows.

Derivation exists for the remaining case: a source that provides **only a code graph, with no native flow data**. There, docforge derives one *from the code graph it already has*. The result is **provisional**: written to `.docforge/tmp/domain-graph.json`, git-ignored, regenerated each run, **never committed**. It unblocks flow docs without depending on any one plugin, and it is grounded in the graph — never invented.

> This is docforge's own derivation. It borrows nothing but the general idea (extract domains/flows/steps from an existing graph) — the prompt and output shape below are docforge's.

## When to run it

`precheck_graph.py --need flow` tells you: `READY` (native or already-derived) → proceed; `MISSING flow graph` while the code graph is present → derive it with the loop below. If the code graph itself is missing, stop — derivation has nothing to work from.

## The loop (agent-mediated)

A script cannot infer business domains, so the reasoning step is a subagent:

1. **Prepare the context.**
   ```
   python scripts/derive_flow_graph.py prepare --repo <path>
   ```
   Resolves the code graph through the registry and writes a compact digest to `.docforge/tmp/domain-context.json`: each node's `id/name/type/path/summary`, the flow-signal edges (`calls`/`imports`/`contains`/`handles`/route/step/entry), and any layers. It also drops `.docforge/tmp/.gitignore` so nothing here is committed.

2. **Dispatch the docforge domain analyzer** (below) on that context. Save its JSON to a file, e.g. `.docforge/tmp/analysis.json`.

3. **Write the flow graph.**
   ```
   python scripts/derive_flow_graph.py write --repo <path> --analysis .docforge/tmp/analysis.json
   ```
   Validates the analyzer output against docforge's flow shape and writes `.docforge/tmp/domain-graph.json`. It refuses an empty `flows` list — if the code graph evidences no flows, that is the honest answer; do not write an invented graph.

4. Re-run `precheck_graph.py --need flow` — it now reports the derived (provisional) flow graph. Docs built from it must note flows are provisional and confirm business rules against source before asserting them.

## The docforge domain analyzer (prompt)

Give the subagent the `domain-context.json` and this instruction:

> You extract business structure from a code graph. Using **only** what the provided graph evidences — nodes, their paths and summaries, and the edges between them — identify the business domains, the flows within them, and each flow's ordered steps. Do not invent a flow, domain, or step that the graph does not support; fewer, well-grounded flows beat a plausible-sounding set. Prefer the code's own business terminology from node names and summaries.
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
> Rules: every flow has a non-empty `name` and a `steps` list; steps are ordered by `order` starting at 1; omit `path` when you cannot tie a step to a file rather than guessing; a flow whose steps you cannot order is still valid as a single step. Return the JSON only.

The `write` subcommand stamps `derived: true`, the `source`, `generatedFrom`, and `generatedAt` — the analyzer supplies only `flows` (and optional `domains`).

## When the code graph came from GitNexus

GitNexus already models execution flows natively, so **read them directly — do not derive.** These processes *are* the flow graph; the derivation loop above is only for a source that carries no such data.

- **Flows + ordered steps** — the `query({query, goal})` MCP tool returns processes (execution flows) with symbols grouped by flow and file locations; the `gitnexus://repo/{name}/processes` resource lists all flows and `gitnexus://repo/{name}/process/{name}` gives the step-by-step trace. Step order is the 1-indexed `step` field on the `STEP_IN_PROCESS` edge (Cypher: `MATCH (s)-[r:CodeRelation {type:'STEP_IN_PROCESS'}]->(p:Process) WHERE p.heuristicLabel = "<flow>" RETURN s.name, r.step ORDER BY r.step`). Offline (no MCP): `graph_source_gitnexus_reader.py --flows`.
- **Domain grouping** — `gitnexus://repo/{name}/clusters` (Leiden `Community` nodes; membership via `MEMBER_OF`). Each `Process` also carries a `communities[]` property and a `processType` of `intra_community` / `cross_community`, so a flow can be mapped to the domain(s) it spans.
- **Caveat** — GitNexus process labels are code-derived (`Entry → Terminal`), not business phrases. Keep them faithful by default; only rename to business language where a node summary clearly supports it, and note it.

Full GitNexus read recipes are in `references/graph-source-gitnexus.md`.
