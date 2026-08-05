# Parallel execution

Parallel work is read-only evidence collection, plus — at the orchestrator's
discretion — artifact-only document writing by spawned sub-agents. The
orchestrator owns planning, merging, manifest state, and final acceptance;
workers never mutate the manifest.

## Safe fan-out

Fan out only across scopes that can be investigated independently:

- functional areas with separate evidence questions;
- distinct flow candidates;
- child repositories;
- independent audits of completed artifacts;
- independent documents in `write_order` whose target files do not collide
  and whose ordering allows concurrency (never a child before the ancestor
  index it must not race, and never two workers on the same file).

Workers must not edit repository files except under the parallel-writing
contract: a spawned writer may materialize and edit **only its own document
artifact** (and may scaffold no shared ancestor index — the orchestrator does
that serially before fan-out). In particular, only the orchestrator mutates
`.docforge/manifest.json`: manifest commands perform unlocked full-file
rewrites, so concurrent writers can silently lose state. This includes the
graph provider: a worker never calls `precheck_graph` or `set-graph` and never
selects or relocks a provider — it consumes the provider/flow already locked
into `manifest["graph"]` and handed to it in its document card (see
[`../workflows/writing.md`](../workflows/writing.md)'s fan-out contract and
[`graph/graph-sources.md`](graph/graph-sources.md) "Session persistence").

Read-only discovery may run before the plan gate. No document writing starts
until the complete tree and document cards pass that gate. Afterward, document
writing follows `write_order`; the orchestrator writes serially or spawns
sub-agents for independent documents in parallel, and applies every status
transition serially in both modes. Manifest initialization,
dynamic additions, status changes, provenance synchronization, and audit
recording are always serial orchestrator operations.

```mermaid
flowchart TD
    A["Define bounded evidence questions"] --> B["Fan out read-only investigations"]
    B --> C["Return result contracts"]
    C --> D["Orchestrator merges and deduplicates"]
    D --> E["Apply manifest mutations serially"]
    E --> F["Display and pass plan gate"]
    F --> G["Write next document in write_order — or spawn sub-agents for independent documents in parallel (artifacts only)"]
    G --> H["Apply status transitions serially"]
    H --> I["Run independent read-only audit"]
    I --> J["Record audit result serially"]
    J --> K{"More documents"}
    K -->|Yes| G
    K -->|No| L["Run whole-tree gate"]
```

## Result contract

Each worker returns one bounded result containing:

- assigned scope and evidence question;
- candidate documents or flows, when applicable;
- claims with source paths, symbols or regions, and graph references;
- confidence, unresolved gaps, and conflicting evidence;
- proposed manifest changes, without applying them;
- audit verdict and defects for audit work.

Results must distinguish observed evidence from synthesis. A worker that cannot
answer its question returns the gap and the retrieval step reached; it does not
expand into an unbounded repository scan.

## Merge and deduplication

The orchestrator normalizes and merges results before any mutation. Deduplicate
source evidence by repository-relative path plus symbol or region, flow
candidates by normalized `entry_ref`, child repositories by canonical root,
and document proposals by manifest id and path. Combine corroborating evidence
without duplicating claims.

Do not silently collapse disagreements. Prefer current direct source over
summaries, record stale graph evidence as stale, and retain unresolved
conflicts for targeted follow-up. Apply the merged manifest proposal once,
redisplay any required structure update, then continue serial execution.
