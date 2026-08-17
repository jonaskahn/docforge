# Flow indexing and derivation

Flow discovery has two layers. The **flow index** lists every evidence-backed
candidate, including deferred work. A **flow document** is a deep analysis of
one main standalone candidate (or a composed parent). Never turn every graph
node or GitNexus Process into a document.

## Build the complete index

Run:

```sh
python3 runtime/cli/python/flow_index.py harvest --repo <repo> \
node runtime/cli/js/flow_index.js harvest --repo <repo> \
# bun  runtime/cli/js/flow_index.js harvest --repo <repo> \
# deno run -A runtime/cli/js/flow_index.js harvest --repo <repo> \
  [--gitnexus-export <mcp-export.json>] [--main-limit 15]

python3 runtime/cli/python/flow_index.py revise --repo <repo> \
node runtime/cli/js/flow_index.js revise --repo <repo> \
# bun  runtime/cli/js/flow_index.js revise --repo <repo> \
# deno run -A runtime/cli/js/flow_index.js revise --repo <repo> \
  [--gitnexus-export <mcp-export.json>] [--main-limit 15]
```

The equivalent Node command uses `flow_index.js` (scripts and README:
[`../../runtime/flows/README.md`](../../runtime/flows/README.md)). Harvest
writes `.docforge/flow-index.json` (schema **1.1**) during repository
discovery with `main` / `deferred` priorities. Revise re-harvests, merges
with the existing index (preserving `documented` and `skipped`), sets other
rows to `placeholder`, creates stub markdown **only for main-priority
standalone** placeholders, prunes orphan scaffold stubs for
deferred/`index_only`/`member` rows, and prints a NOTICE listing main
standalone flows eligible for full documentation.

Bare verb symbols (`get`, `save`, `create`, …) receive deterministic
`{module}-{symbol}` slugs when a module path is available, so the docs tree
is not flooded with `save-2.md`-style collisions.

After the manifest tree has passed the plan gate and `flows_index` reaches
its write turn, run `flow_index.{py,js} render --repo <repo>` to project that
machine record into `docs/flows/README.md`. Rendering is document writing and
never precedes the plan gate.

For GitNexus, export `Route`, `Process`, and `Community` properties through
its MCP/cypher interface. Processes are heuristic Entry-to-Terminal paths,
not business flows. Group them by `entryPointId`, retain the terminal set and
community crossing as reach evidence, and emit one candidate per entry.
Community **IDs** stay distinct for boundary/reach math; area strings and the
compact `.docforge/tmp/communities.md` table collapse duplicate
`heuristicLabel` values so agent/LLM analysis is not flooded. Harvest and
revise also merge near-duplicate candidates after exact `entry_ref` merge:
same `filePath` + `slugify(name)`, or the same lowercased signature. On
merge, union evidence and unique area labels; prefer confirmed confidence.
The deterministic interchange object is:

```json
{
  "routes": [{"id": "route-id", "path": "GET /items", "filePath": "src/api.ts", "symbol": "listItems"}],
  "processes": [{"id": "proc-id", "entryPointId": "Function:src/api.ts:listItems", "terminalId": "Function:src/db.ts:query", "processType": "cross_community", "stepCount": 4, "communities": ["comm-api", "comm-db"]}],
  "communities": [{"id": "comm-api", "heuristicLabel": "API"}]
}
```

For Understand Anything, native `domain-graph.json` flow nodes are confirmed
candidates. They are authoritative but may be incomplete. Scan
`knowledge-graph.json` for additional candidates through presentation/API and
application/service layer membership, tour context, and entry-like
file/symbol names. A knowledge graph containing only `contains` edges
supplies structure, not an ordered call flow.

Every row records a normalized `entry_ref`, evidence, confidence, reach,
rank, `priority` (`main` or `deferred`), status (`main`, `deferred`,
`placeholder`, `documented`, or `skipped`), and organization fields:

| Field | Meaning |
| --- | --- |
| `display_name` | Reader-recognizable outcome (not a bare symbol) |
| `family` | Optional kebab group/folder key (`email`, `content`) |
| `doc_role` | `standalone` (own deep-dive), `member` (composed into parent), `index_only` (no stub) |
| `composed_into` | Parent flow id when `doc_role` is `member` |
| `doc_path` | Markdown path under `docs/flows/` (null for member/index_only) |

Harvest defaults: main → `standalone` + `docs/flows/{slug}.md`; deferred →
`index_only` + null path. Only main-priority **standalone** rows may be added
as dynamic deep-dive documents in the manifest. Deferred/`index_only` rows
stay in the index until promoted. Members stay in the index under their
parent.

## Organize names, families, and composition

After `harvest` or `revise`, and **before** deep-dive analysis, run the
organize step so naming and grouping are settled:

```sh
python3 runtime/cli/python/flow_index.py organize emit --repo <repo>
node runtime/cli/js/flow_index.js organize emit --repo <repo>
# bun  runtime/cli/js/flow_index.js organize emit --repo <repo>
# deno run -A runtime/cli/js/flow_index.js organize emit --repo <repo>
# Agent writes .docforge/tmp/flow-organization.json from the pack
python3 runtime/cli/python/flow_index.py organize apply --repo <repo> \
node runtime/cli/js/flow_index.js organize apply --repo <repo> \
# bun  runtime/cli/js/flow_index.js organize apply --repo <repo> \
# deno run -A runtime/cli/js/flow_index.js organize apply --repo <repo> \
  --organization .docforge/tmp/flow-organization.json
```

`organize emit` writes a compact pack
(`.docforge/tmp/flow-organization-pack.json`) with entry refs, module hints,
ranks, and organization rules. The agent/LLM proposes:

- descriptive `display_name` / `slug` values
- `family` keys and optional `docs/flows/{family}/…` paths
- composition groups: small related ops become `doc_role: member` with
  `composed_into` pointing at a standalone parent (use `compose_members` on
  the parent update)

`organize apply` validates stable ids, slug uniqueness, and path shape;
updates the index; moves or refreshes stubs; and prunes orphan scaffolds.

### Layout rules

- **Name** = business outcome; file slug = kebab of that name.
- **Compose** into one markdown when members are small endpoint/service ops
  sharing a domain (email create/update/upload/notice → H2 sections under
  one parent).
- **Family folder** when ≥3 documentable siblings or composed parents share a
  domain (`docs/flows/email/…`).
- **Main budget** (`--main-limit`) still caps deep-dives; members do not
  consume separate deep-dive slots.
- README render groups by family; deferred/`index_only` rows list without
  stub files.

Human shorthand: **primary** ≈ main + standalone/parent; **secondary** ≈
member composed into a parent, or deferred index-only. Do not invent a
parallel priority enum.

## Derive main-flow detail

Use this procedure after organize (when needed) and `flow_index.{py,js}
harvest` / `revise` when main standalone rows need deep analysis. The
agent/LLM performs the reasoning step; scripts only prepare compact context
and validate JSON.

1. Prefer the post-dedup analysis pack:
   - main-priority **standalone** rows from `.docforge/flow-index.json` (rank order)
   - `.docforge/tmp/communities.md` / `communities.json` when present
   - existing documented flow docs that need re-grounding
2. When the chosen provider has a code graph but no native flow graph, also
   run `derive_flow_graph.{py,js} prepare --repo <repo>` for the bounded
   code-graph digest (see
   [`../../runtime/flows/README.md`](../../runtime/flows/README.md)) in
   `.docforge/tmp/flow-context.json`.
3. Agent/LLM analyzes **main standalone only**. For each flow record actors,
   trigger, ordered steps, branches, rules, failures, and outcome. Write
   `.docforge/tmp/flow-analysis.json` in the shape expected by
   `derive_flow_graph.{py,js} write` (see the `derive_flow_graph.py|js`
   docstring).
4. When a provisional graph is required, run
   `derive_flow_graph.{py,js} write --repo <repo> --analysis
   .docforge/tmp/flow-analysis.json`.
5. Treat `.docforge/tmp/flow-graph.json` as provisional. Confirm business
   rules against source before asserting them in deep-dive flow documents.
6. Rerun `precheck_graph.{py,js} --repo <repo> --need flow` (see
   [`../../runtime/graph/README.md`](../../runtime/graph/README.md)) before
   writing documents that require `flow_graph`.

Containment edges never establish execution order. The derived file is
temporary, git-ignored, and regenerated when needed. Native provider detail
takes precedence. Do not feed the raw per-ID community dump to the analyzer;
always use the deduplicated label summary.

## Cross-repository use

`entry_ref` is the durable join surface for Portfolio analysis. Normalize
HTTP routes, queue/topic names, schedules, and CLI commands so an outbound
boundary in one member repository can match an inbound flow entry in
another. Preserve the original signatures in evidence; do not claim a
cross-repository link from name similarity alone.
