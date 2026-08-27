# Flows runtime

Flow-candidate harvesting, surface-aware preflight, and provisional flow-graph derivation. `flow_index`
maintains the durable `.docforge/flow-index.json`; `flow_preflight` maintains
the lossless `.docforge/flow-evidence.json`; `derive_flow_graph` bridges
a code graph into a provisional, agent-produced flow graph when no native flow
graph exists. Both are paired Python/JS public commands.

## Load this when

- Discovering every evidence-backed flow candidate → `flow_index harvest`.
- Building or refreshing runtime-surface topology before selection →
  `flow_preflight prepare`.
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
| `flow_analysis` | both | CLI | Prepare/import/decide/status/validate/audit the adaptive deep flow pack (schema v3) |
| `flow_preflight` | both | CLI | Prepare/import/status/validate the persistent runtime-surface topology ledger (schema 1.0) |
| `derive_flow_graph` | both | CLI | Prepare context + write a provisional flow graph |
| `budgets` | both | Module | Scale-aware flow budget defaults read from `project.scale.class` |

## Details

### `flow_index`

Emitted flow documents and stubs follow `project.provenance_storage`:
`json` stamps the folder sidecar and leaves clean markdown; `markdown`
emits inline frontmatter.

```sh
python3 runtime/cli/python/flow_index.py <harvest|revise|update|import|apply-analysis|organize|render> --repo <repo> \
  [--main-limit N] [--output <path>] [--organization <json>] \
  [--id <flow-id>] [--priority main|deferred] [--status main|deferred|placeholder|skipped] \
  [--summary <text>] [--written] [--analysis <flow-analysis.json>]
```

`apply-analysis` reads the frozen v3 pack, updates matching rows' canonical
names, hierarchy, and `analysis_state`, and adds only approved decomposition
children. It runs before the serial `update` and `manage_manifest add` steps.

### `flow_analysis`

The persistent `.docforge/flow-analysis.json` ledger owns adaptive per-flow
evidence and document design: reader question, trigger, guarantee, actors,
terminal outcomes, ordered source-located steps, decisions/waits/loops/joins,
characteristic modules, failure and residual state, conflicts, gaps, research
questions, and decomposition proposals.

```sh
python3 runtime/cli/python/flow_analysis.py <prepare|import|decide|status|validate|audit> --repo <repo> \
  [--manifest <path>] [--json] [--analysis <path>] \
  [--select <ids>] [--decline <ids>] [--approve-decomposition <proposal-ids>] \
  [--research-policy official-primary|official-only|off] \
  [--verdict PASS|FAIL] [--report <path>]
```

New packs always use schema v3. V1/V2 packs remain readable but their flows
become `legacy-needs-analysis`; the migration preserves legacy evidence without
synthesizing missing deep facts.

### `flow_preflight`

```sh
python3 runtime/cli/python/flow_preflight.py <prepare|import|status|validate> --repo <repo> \
  [--json] [--input <enrichment.json>]
```

`prepare` records runtime surfaces (request/event/schedule/UI/command/library/
lifecycle/operation/internal), provider provenance, graph roots, independent
path variants, terminals, divergence/rejoin/cycle markers, and typed gaps in
the committed `.docforge/flow-evidence.json`. It reuses manifest profiles,
`detect_profiles`, and the architecture ledger when available. `import` adds
MCP/source enrichment without replacing unchanged entries; entry-specific
fingerprints leave unaffected enrichment in place and mark changed entries
stale/not-analyzed. `status` reports complete, stale, ambiguous, and unresolved
entries. `validate` rejects dangling topology/provenance, while incomplete
candidates remain selectable but cannot become analysis-ready.

`flow_index harvest` and `revise`, plus `flow_analysis prepare`, refresh this
ledger automatically whenever their locked/on-disk CodeGraph or GitNexus input
is readable. The explicit command remains useful for inspection and importing
targeted MCP/source enrichment.

`--main-limit` (harvest / revise / import) defaults are **scale-aware**: the
deep-dive document budget follows `project.scale.class` from the manifest
(small 15, medium 25, large 40; fallback 15 when the manifest is missing or
names an unknown class). An explicit `--main-limit` always wins; 0 /
negative counts as "not passed". The harvest/revise/import summary line
prints the resolved budget (`main budget 40 — scale large`).

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
  history; **writes** `.docforge/flow-index.json` (schema 1.4). With a GitNexus
  interchange it also writes `.docforge/tmp/communities.md|.json`. When a
  CodeGraph/GitNexus preflight ledger exists, it consumes that ledger first;
  legacy provider readers remain a compatibility fallback. Main-flow ranking is
  coverage then score: one strong candidate per runtime surface is reserved
  before the remaining budget is ranked. Does not create flow-document stubs.
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

The default main budget follows `project.scale.class` (small 15, medium 25,
large 40; fallback 15). Confirmed native flows rank above candidates.

### `derive_flow_graph`

```sh
python3 runtime/cli/python/derive_flow_graph.py prepare --repo <repo> [--max-flows N] [--hops N]
python3 runtime/cli/python/derive_flow_graph.py write --repo <repo> --analysis <analysis.json>
```

`--max-flows` (prepare) defaults to the same scale-aware scheme as
`--main-limit`: small 15, medium 30, large 50 per `project.scale.class`
(fallback 15); an explicit value always wins.

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
| `flow_analysis` | [`workflows/planning.md`](../../workflows/planning.md), [`workflows/writing.md`](../../workflows/writing.md), [`workflows/revision.md`](../../workflows/revision.md) | `flow_index apply-analysis` consumes approved hierarchy/readiness |
| `derive_flow_graph` | [`workflows/revision.md`](../../workflows/revision.md), [`references/graph/flow-derivation.md`](../../references/graph/flow-derivation.md), [`references/graph/adding-a-graph-source.md`](../../references/graph/adding-a-graph-source.md) | `graph/precheck_graph` (remediation step), `graph/graph_storage` (write helpers) |

## Boundaries

Flow *mechanics* live here; provider readiness and selection policy live in
[`../graph/README.md`](../graph/README.md) and
[`../../references/graph/flow-derivation.md`](../../references/graph/flow-derivation.md).
Artifacts: `.docforge/flow-evidence.json`, `.docforge/flow-index.json`, `.docforge/flow-analysis.json`,
`.docforge/tmp/` files, `docs/flows/`.
