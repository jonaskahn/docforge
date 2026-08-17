# Flows runtime

Flow-candidate harvesting and provisional flow-graph derivation. `flow_index`
maintains the durable `.docforge/flow-index.json`; `derive_flow_graph` bridges
a code graph into a provisional, agent-produced flow graph when no native flow
graph exists. Both are paired Python/JS public commands.

## Load this when

- Discovering every evidence-backed flow candidate → `flow_index harvest`.
- Re-running the flow index with preserved state → `flow_index revise`.
- Applying the write-start selection gate (promote / demote / skip rows) or
  writing back a completed flow's summary → `flow_index update`.
- Seeding derived candidates from agent flow analysis (CodeGraph-only / no
  native flow source) → `flow_index import`.
- Asking the user to organize/rank flows → `flow_index organize emit` → `organize apply`.
- Rendering the flow matrix → `flow_index render`.
- `precheck_graph --need flow` found a code graph but **no** native or derived
  flow graph → `derive_flow_graph prepare` then `write`.

## Scripts

| Script | js/py | Kind | Purpose |
|---|---|---|---|
| `flow_index` | both | CLI | Harvest/revise/update/import/organize/render the durable flow candidate index |
| `derive_flow_graph` | both | CLI | Prepare context + write a provisional flow graph |

## Details

### `flow_index`

Emitted flow documents and stubs follow `project.provenance_storage`:
`json` stamps the folder sidecar and leaves clean markdown; `markdown`
emits inline frontmatter.

```sh
python3 runtime/cli/python/flow_index.py <harvest|revise|update|import|organize|render> --repo <repo> \
  [--main-limit N] [--output <path>] [--organization <json>] \
  [--id <flow-id>] [--priority main|deferred] [--status main|deferred|placeholder|skipped] \
  [--summary <text>] [--written] [--analysis <flow-analysis.json>]
```

There are **no provider flags** — but there is a lock. When
`manifest["graph"]` records a provider, `harvest` collects that provider's flow
evidence; other providers' artifacts are not harvested even when present (it
falls through to them only if the locked provider yields nothing, and says so in
`sources`). Without a lock, flows come from whatever flow evidence the
repository holds. Understand Anything `.ua/domain-graph.json` /
`.ua/knowledge-graph.json` are read in place; GitNexus flows arrive as the
auto-discovered interchange `.docforge/tmp/gitnexus-flows.json`
(`{routes, processes, communities}` — the agent materializes it from the
GitNexus MCP or the offline lbug reader, see
[`../../references/graph/graph-source-gitnexus.md`](../../references/graph/graph-source-gitnexus.md)).

- `harvest` — reads Understand Anything graphs, the discovered GitNexus
  interchange, and git
  history; **writes** `.docforge/flow-index.json` (schema 1.2). With a GitNexus
  interchange it also writes `.docforge/tmp/communities.md|.json`. Does not create
  flow-document stubs.
- `revise` — re-harvests, preserves `documented`/`skipped` state and written
  `summary`/`written_at` fields, refreshes `docs/flows/` placeholder stubs,
  deletes orphan scaffolds; never overwrites a completed non-placeholder
  document. A 1.1 index is upgraded additively on load.
- `update` — the mechanical apply step for the write-start selection gate and
  the post-write summary write-back. `--priority` / `--status` set the row's
  selection outcome (promote → `main`/`placeholder`; demote →
  `deferred`/`deferred`; decline → `skipped`) and normalize `doc_role` /
  `doc_path` accordingly; `--summary` stamps the one-paragraph outcome
  summary and `written_at` on a **documented** row (refused otherwise);
  `--written` alone refreshes `written_at`. Orchestrator-only, serial — never
  run by a parallel document writer.
- `import` — seeds derived candidates when the code graph has no native
  flows: maps agent flow-analysis entries (`name`, `entryPoint`?, `domain`?,
  `steps`) onto `candidate` rows, finalizes rank/slug/main budget, then
  merges with the existing index through the same state-preserving merge
  `revise` uses. Documented/skipped rows keep their status, summaries, and
  organization; new rows land as `placeholder` rows awaiting the selection
  gate. Evidence points at `.docforge/tmp/flow-graph.json`.
- `organize emit` — writes `.docforge/tmp/flow-organization-pack.json`.
- `organize apply` — validates and applies organization (names, slugs,
  families, roles, paths); may move/copy/delete flow files; rewrites the index.
- `render` — writes `docs/flows/README.md` (default) with provenance
  referencing the index; documented rows with a written `summary` also
  appear in the rendered `Flow summaries` section.

Default main budget is 15 flows. Confirmed native flows rank above candidates.

### `derive_flow_graph`

```sh
python3 runtime/cli/python/derive_flow_graph.py prepare --repo <repo> [--max-flows N] [--hops N]
python3 runtime/cli/python/derive_flow_graph.py write --repo <repo> --analysis <analysis.json>
```

- `prepare` — uses the session's locked code provider (`resolve_locked`), falling
  back to registry priority only when no lock exists; JSON sources get
  bounded entry-point clusters, DB/MCP sources get native-interface/MCP
  exploration instructions. Records which it was as `sourceOrigin` and prints it
  (`source: codegraph [session lock]`). A lock whose graph has left the disk
  fails with exit 1 and the `set-graph --force` remedy rather than silently
  using another provider. **Writes** ignored `.docforge/tmp/flow-context.json`.
- `write` — validates the agent analysis (non-empty `flows`, each with `name`
  and `steps`) and **writes** ignored `.docforge/tmp/flow-graph.json`
  (`derived: true` + provenance).

The result is explicitly provisional and never intended for commit. Do not use
this when a native UA/GitNexus flow graph is available.

## Where invoked

| Script | Documented callers | Programmatic callers |
|---|---|---|
| `flow_index` | [`workflows/revision.md`](../../workflows/revision.md), [`workflows/tools.md`](../../workflows/tools.md), [`references/graph/graph-sources.md`](../../references/graph/graph-sources.md), [`references/graph/flow-derivation.md`](../../references/graph/flow-derivation.md) | `manifest/manage_manifest add` (flow docs update the index) |
| `derive_flow_graph` | [`workflows/revision.md`](../../workflows/revision.md), [`references/graph/flow-derivation.md`](../../references/graph/flow-derivation.md), [`references/graph/adding-a-graph-source.md`](../../references/graph/adding-a-graph-source.md) | `graph/precheck_graph` (remediation step), `graph/graph_storage` (write helpers) |

## Boundaries

Flow *mechanics* live here; provider readiness and selection policy live in
[`../graph/README.md`](../graph/README.md) and
[`../../references/graph/flow-derivation.md`](../../references/graph/flow-derivation.md).
Artifacts: `.docforge/flow-index.json`, `.docforge/tmp/` files, `docs/flows/`.
