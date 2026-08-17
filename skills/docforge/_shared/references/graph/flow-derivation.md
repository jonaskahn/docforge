# Flow indexing and derivation

Flow discovery has two layers. The **flow index** lists every evidence-backed
candidate, including deferred work. A **flow document** is a deep analysis of
one main standalone candidate (or a composed parent). Never turn every graph
node or GitNexus Process into a document.

## What counts as a step

A step is **one hop in the graph, carrying a `file` and (where the source has
it) a `line`**. "Content is indexed into Elasticsearch → `src/lib/utils/searchUtils.lib.js`"
is a paraphrase of a subsystem, not a step; `indexContent` at
`src/lib/utils/searchUtils.lib.js:88` is a step.

The division of labour follows from that:

| Layer | Owns | Never |
|---|---|---|
| The scripts | Entry-point ranking, ordered call chains, `file:line` per hop | Business naming |
| The agent/LLM | Outcome, actors, branch conditions, rules, failures | Inventing step order |

If the graph cannot evidence an ordered chain, say so in the index and leave
the flow a `candidate` — do not narrate one. Every step in a v2 analysis
records `evidence: "graph"` (walked out of the code graph) or
`"source"` (read in a file); a step with neither a locator nor a source
citation is not a documented step.

## Build the complete index

Run:

```sh
python3 runtime/cli/python/flow_index.py harvest --repo <repo> \
node runtime/cli/js/flow_index.js harvest --repo <repo> \
# bun  runtime/cli/js/flow_index.js harvest --repo <repo> \
# deno run -A runtime/cli/js/flow_index.js harvest --repo <repo> \
  [--main-limit 15]

python3 runtime/cli/python/flow_index.py revise --repo <repo> \
node runtime/cli/js/flow_index.js revise --repo <repo> \
# bun  runtime/cli/js/flow_index.js revise --repo <repo> \
# deno run -A runtime/cli/js/flow_index.js revise --repo <repo> \
  [--main-limit 15]
```

There are no provider flags — but the session lock decides whose evidence is
read. With a provider locked in `manifest["graph"]`, harvest collects that
provider's flow evidence and leaves other providers' artifacts alone (falling
through only if the locked provider yields nothing, and naming the fallback in
`sources`). Without a lock, harvest and revise discover whatever flow
evidence the repository holds. Understand Anything `.ua/domain-graph.json`
and `.ua/knowledge-graph.json` are read in place. GitNexus flows arrive as
the auto-discovered interchange `.docforge/tmp/gitnexus-flows.json` (see
below). A code graph without native flows contributes derived candidates
through `flow_index import --analysis` (see "Derived candidates").

The equivalent Node command uses `flow_index.js` (scripts and README:
[`../../runtime/flows/README.md`](../../runtime/flows/README.md)). Harvest
writes `.docforge/flow-index.json` (schema **1.2**; a 1.1 index is upgraded
additively on load) during repository
discovery with `main` / `deferred` priorities. Revise re-harvests, merges
with the existing index (preserving `documented`, `skipped`, written
`summary` / `written_at`), sets other
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

For GitNexus, the deterministic interchange at
`.docforge/tmp/gitnexus-flows.json` is produced by a **command**, not by hand:

```sh
python3 runtime/cli/python/graph_source_gitnexus_reader.py --repo <repo> --interchange
node runtime/cli/js/graph_source_gitnexus_reader.js --repo <repo> --interchange
```

or by emitting the same shape from the GitNexus MCP/cypher interface
([`graph-source-gitnexus.md`](graph-source-gitnexus.md)). Harvest discovers it
automatically; there is no CLI flag. When a GitNexus index is ready and the
interchange is absent, `flow_index harvest` now **fails naming this command**
rather than silently skipping a native flow source.

The interchange carries `Route`, `Process`, and `Community` properties.
Processes are heuristic Entry-to-Terminal paths, not business flows. Group them
by `entryPointId`, retain the terminal set and community crossing as reach
evidence, and emit one candidate per entry. Each process carries its ordered
`STEP_IN_PROCESS` steps; harvest merges them across processes sharing an entry,
de-duplicating the shared early hops, and stores the sequence in `evidence`.
`stepCount` remains the fallback for an interchange produced without `steps`.
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
  "processes": [{"id": "proc-id", "entryPointId": "Function:src/api.ts:listItems", "terminalId": "Function:src/db.ts:query", "processType": "cross_community", "stepCount": 4, "communities": ["comm-api", "comm-db"],
                 "steps": [{"order": 1, "nodeId": "Function:src/api.ts:listItems", "filePath": "src/api.ts", "symbol": "listItems"}]}],
  "communities": [{"id": "comm-api", "heuristicLabel": "API"}]
}
```

`steps` is optional for back-compatibility, but an interchange without it
reduces a native ordered process to a number.

For Understand Anything, native `domain-graph.json` flow nodes are confirmed
candidates. They are authoritative but may be incomplete. Scan
`knowledge-graph.json` for additional candidates through presentation/API and
application/service layer membership, tour context, and entry-like
file/symbol names. A knowledge graph containing only `contains` edges
supplies structure, not an ordered call flow.

## Derived candidates

When the selected code graph has no native flow evidence (CodeGraph-only,
or any provider without native flows), flows still come from the available
code graph — the candidates are derived, then imported into the index so
the write-start selection gate works for every provider.

**CodeGraph is not data-free here.** `graph_source_codegraph_reader` reads
`.codegraph/codegraph.db` read-only and supplies ranked entry points plus
ordered call chains, so `harvest` works on a CodeGraph-only repository and
`prepare` emits real clusters instead of an instruction to go look. Each
cluster's `paths` are ordered hops with `file` and `line` — the step skeleton.
The analyzer's job is to name the outcome and confirm branches, rules, and
failures against source or `codegraph_explore`, **not** to invent the order.

Two limits worth knowing before writing:

- Chains stop where CodeGraph stops. Method dispatch through a service object
  (`contentService.getActivities()`) resolves to the object, not the method, so
  a chain can end at a `constant`. Continue from there by reading the file.
- A self-recursive handler is a one-hop chain, not a deep one; the walk's cycle
  guard is why. Without it a single self-edge fabricates a chain to the depth
  limit.

```sh
python3 runtime/cli/python/derive_flow_graph.py prepare --repo <repo> \
node runtime/cli/js/derive_flow_graph.js prepare --repo <repo> \
# …then the agent/LLM analyzes main flows into .docforge/tmp/flow-analysis.json…
python3 runtime/cli/python/flow_index.py import --repo <repo> \
node runtime/cli/js/flow_index.js import --repo <repo> \
# bun  runtime/cli/js/flow_index.js import --repo <repo> \
# deno run -A runtime/cli/js/flow_index.js import --repo <repo> \
  --analysis .docforge/tmp/flow-analysis.json [--main-limit 15]
```

### The analysis pack (schema 2)

Write `.docforge/tmp/flow-analysis.json` in this shape. The older v1 shape
(`{name, entryPoint?, domain?, steps[{order, name, path?}]}`) still imports,
but it has nowhere to put six of the seven facts
[`../../content/flows/flow.contract.md`](../../content/flows/flow.contract.md)
requires, so everything but the name and a step count was discarded on import.

```json
{ "schemaVersion": 2, "source": "codegraph",
  "flows": [{
    "name": "Crop an uploaded image",
    "domain": "ai",
    "outcome": "Caller receives a smart-cropped image derived from the upload",
    "trigger": {"kind": "http", "signature": "POST /smartCrop"},
    "actors": ["API client", "AI service"],
    "entryPoint": {"symbol": "smartCrop", "file": "src/modules/ai/ai.routes.js",
                   "line": 12, "nodeId": "route:1"},
    "steps": [{"order": 1, "name": "Route accepts the upload",
               "file": "src/modules/ai/ai.routes.js", "line": 12,
               "symbol": "smartCrop", "nodeId": "route:1", "evidence": "graph"}],
    "branches": [{"afterStep": 2, "condition": "payload missing image",
                  "goesTo": "400 response", "file": "…", "line": 44}],
    "rules":    [{"statement": "Images above 10MB are rejected", "file": "…", "line": 47}],
    "failures": [{"trigger": "vision API timeout", "handling": "retry once then 502",
                  "file": "…", "line": 96}]
  }]}
```

v2 requires `trigger.kind`, `outcome`, and a `file` on every step; import
refuses the pack otherwise and writes nothing.

`import` builds `entry_ref` from `entryPoint` — signature and file from the
same place, so the two can no longer disagree — sets `confidence: confirmed`
only when **every** step carries a graph `nodeId` (so an LLM-only flow never
outranks a graph-derived one), derives `reach.boundaries` from the distinct
top-level directories the steps span, and copies steps, branches, rules,
failures, actors, and outcome into `evidence`.

The validated pack is then persisted to **`.docforge/flow-analysis.json`**,
outside `tmp/` so it survives the run that produced it; the flow writer reads
it instead of re-deriving by grep. Rows are finalized (rank / slug / main
budget), then merged with the existing index through the same
state-preserving merge `revise` uses — documented and skipped rows keep
their status, summaries, and organization; new rows land as `placeholder`
rows awaiting the selection gate. Derived evidence is provisional: confirm
business rules against source before publishing deep-dive flow documents.

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

## Selection gate and write-back

Which harvested candidates become deep-dive documents is a **user
decision at write start** (fresh start: after the plan gate, before
writing; revise flow: after the flow-mode question and analysis). The
gate is mandatory — `--auto-accept` never waives it; the user must
choose to proceed. See the owning workflows:
[`../../workflows/planning.md`](../../workflows/planning.md) "Flow gate
(write-start)" and [`../../workflows/revision.md`](../../workflows/revision.md)
"`/docforge-revise flow`".

- **Analysis depth.** Main-priority standalone rows get the full deep
  analysis pack (steps, branches, rules, failures). Deferred rows get
  summary-level context only — name, trigger, entry ref, reach, one-line
  evidence — enough to decide promotion. A promoted row is deep-analyzed
  before writing.
- **Prompt.** Every candidate listed; main standalone pre-selected;
  deferred promotable; budget = `--main-limit` (default 15) deep-dives,
  exceeding it needs explicit confirmation.
- **Apply.** Mechanically with `flow_index.{py,js} update`:
  promote → `--priority main --status placeholder`; demote →
  `--priority deferred`; decline → `--status skipped`. The command
  normalizes `doc_role` / `doc_path` to match: promoted rows become
  `standalone` with a `docs/flows/{slug}.md` path; skipped/demoted rows
  become `index_only` with no path. On a revise flow,
  `flow_index.{py,js} revise` into the real index runs **first** — a
  row the re-harvest introduced does not exist in the real index yet,
  and `update` fails on an unknown id; on a fresh start, `harvest`
  already wrote the real index, so no revise step is needed. Then
  `manage_manifest.{py,js} add --type flow` for each selected
  standalone.
- **Write-back.** After a flow document passes lint and its independent
  audit, the orchestrator runs
  `flow_index.{py,js} update --id <flow-id> --summary "<one-paragraph
  outcome>" --written` — refused unless the row is `documented`. The
  rendered matrix shows these summaries in its `Flow summaries` section.
  Never run by a parallel writer; the index stays orchestrator-serial.

## Flow pipeline

The full pipeline is identical in fresh-start planning and
`/docforge-revise flow`; only the harvest mode and the prompt's per-row
actions differ. Fresh start: after the plan gate, before the first
document write. Revise: after the flow-mode question and analysis. The
mandatory selection gate and its `update` mapping live in "Selection
gate and write-back" above.

1. **Precheck** — `precheck_graph.{py,js} --repo <repo> --need flow`.
   Native flow graph first; CodeGraph-only → Docforge-derived
   (provisional).
2. **Harvest or import** — native flow evidence: `flow_index.{py,js}
   harvest` (fresh start, re-analyze) or `revise` (reuse). No native
   flow evidence (CodeGraph-only): `derive_flow_graph.{py,js} prepare`,
   then the agent/LLM analyzes the bounded candidates **once** into
   `.docforge/tmp/flow-analysis.json`, then `flow_index.{py,js} import
   --analysis` seeds the derived rows through the same
   state-preserving merge revise uses. This analysis is the deep pack —
   step 4 must not re-run it.
3. **Organize** — `organize emit`, the agent writes
   `.docforge/tmp/flow-organization.json`, `organize apply`. Naming and
   grouping settle before the prompt — the user never chooses among
   bare symbols.
4. **Analyze** — main-priority **standalone** rows get the full deep
   pack ("Derive main-flow detail" below); run `derive_flow_graph
   write` only when a provisional flow graph is required. Deferred rows
   get summary-level context only. CodeGraph-only: the step-2 analysis
   is the pack; do not analyze twice.
5. **Selection gate** — mandatory; prompt, budget, and mapping above.
6. **Apply** — in this exact order:
   1. `flow_index.{py,js} revise` into the real index on a revise flow
      (upsert every harvested row, preserve `documented` / `skipped`
      state, set other rows to `placeholder`, create stub markdown only
      for main-priority standalone placeholders, prune orphan
      scaffolds). Fresh start: `harvest` already wrote the real index —
      no revise step.
   2. `flow_index.{py,js} update` per changed row (promote / demote /
      decline). Never update before revise: newly harvested rows do not
      exist in the real index yet.
   3. `manage_manifest.{py,js} add --type flow` for each selected
      standalone.
   4. Show the annotated plan tree / structure update; honor the
      execution-mode checkpoint.
7. **Write** — flow documents in `write_order`; a spawned writer edits
   only its own flow document, the index and the manifest stay
   orchestrator-serial.
8. **Write-back** — after lint + independent audit: `flow_index update
   --id <flow-id> --summary "<one-paragraph outcome>" --written`
   (refused unless `documented`).
9. **Render and refresh** — `flow_index render` the matrix (its `Flow
   summaries` section carries the write-backs); update any selected
   overview / index docs whose flow counts or links changed.

Harvest, revise, and import write **metadata only** — the flow index
and placeholder stubs, never user content — so they run in the
repository itself before the gate; there is no provisional copy. The
gate still always precedes `update`, `manage_manifest add`, and every
document write.

**Fresh start vs revise:**

| Step | Fresh start (planning) | `/docforge-revise flow` |
|---|---|---|
| Harvest | `harvest` — full; every row re-derived | Re-analyze: `harvest`; Reuse: `revise` (missing candidates only; stored status, summaries, organization reused) |
| Analyze | Deep pack for main standalone rows | Re-analyze: full deep pack for main standalone rows; Reuse: deep pack only for missing and newly promoted rows |
| Gate | Every candidate; main standalone pre-selected; promote / demote / skip | Per-row actions add / remove / update; unchanged rows are baseline facts |
| Apply | update → add (harvest wrote the index) | revise → update → add |

**Tier rule.** The gate fires only for `diligence` and `portfolio`. At
`spine` the harvest still ran during repository inspection, but
`docs/flows/README.md` renders the candidate matrix only — no gate, no
selection prompt, no flow deep-dives.

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
   trigger, ordered steps, branches, rules, failures, and outcome — the full
   schema-2 pack above, which is the only shape with a slot for all seven.
   Take the step order and each step's `file:line` from the cluster `paths`;
   supply naming and the branch/rule/failure semantics yourself. Write
   `.docforge/tmp/flow-analysis.json`.
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
