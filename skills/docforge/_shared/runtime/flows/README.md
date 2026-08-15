# Flows runtime

Flow-candidate harvesting and provisional flow-graph derivation. `flow_index`
maintains the durable `.docforge/flow-index.json`; `derive_flow_graph` bridges
a code graph into a provisional, agent-produced flow graph when no native flow
graph exists. Both are paired Python/JS public commands.

## Load this when

- Discovering every evidence-backed flow candidate → `flow_index harvest`.
- Re-running the flow index with preserved state → `flow_index revise`.
- Asking the user to organize/rank flows → `flow_index organize emit` → `organize apply`.
- Rendering the flow matrix → `flow_index render`.
- `precheck_graph --need flow` found a code graph but **no** native or derived
  flow graph → `derive_flow_graph prepare` then `write`.

## Scripts

| Script | js/py | Kind | Purpose |
|---|---|---|---|
| `flow_index` | both | CLI | Harvest/revise/organize/render the durable flow candidate index |
| `derive_flow_graph` | both | CLI | Prepare context + write a provisional flow graph |

## Details

### `flow_index`

Emitted flow documents and stubs follow `project.provenance_storage`:
`json` stamps the folder sidecar and leaves clean markdown; `markdown`
emits inline frontmatter.

```sh
python3 runtime/cli/python/flow_index.py <harvest|revise|organize|render> --repo <repo> \
  [--gitnexus-export <json>] [--main-limit N] [--output <path>] [--organization <json>]
```

- `harvest` — reads Understand Anything `.ua/domain-graph.json` /
  `.ua/knowledge-graph.json` (optionally a GitNexus MCP export) and git
  history; **writes** `.docforge/flow-index.json` (schema 1.1). With a GitNexus
  export it also writes `.docforge/tmp/communities.md|.json`. Does not create
  flow-document stubs.
- `revise` — re-harvests, preserves `documented`/`skipped` state, refreshes
  `docs/flows/` placeholder stubs, deletes orphan scaffolds; never overwrites a
  completed non-placeholder document.
- `organize emit` — writes `.docforge/tmp/flow-organization-pack.json`.
- `organize apply` — validates and applies organization (names, slugs,
  families, roles, paths); may move/copy/delete flow files; rewrites the index.
- `render` — writes `docs/flows/README.md` (default) with provenance
  referencing the index.

Default main budget is 15 flows. Confirmed native flows rank above candidates.

### `derive_flow_graph`

```sh
python3 runtime/cli/python/derive_flow_graph.py prepare --repo <repo> [--max-flows N] [--hops N]
python3 runtime/cli/python/derive_flow_graph.py write --repo <repo> --analysis <analysis.json>
```

- `prepare` — uses the registry's first ready code provider; JSON sources get
  bounded entry-point clusters, DB/MCP sources get native-interface/MCP
  exploration instructions. **Writes** ignored `.docforge/tmp/flow-context.json`.
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
