# Flow indexing and derivation

Flow discovery has two layers. The **flow index** lists every evidence-backed
candidate, including deferred work. A **flow document** is a deep analysis of
one main candidate. Never turn every graph node or GitNexus Process into a
document.

## Build the complete index

Run:

```sh
python scripts/flow_index.py harvest --repo <repo> \
  [--gitnexus-export <mcp-export.json>] [--main-limit 15]
```

The equivalent Node command uses `flow_index.js`. Harvest writes
`.docforge/flow-index.json` during repository discovery. After the manifest
tree has passed the plan gate and `flows_index` reaches its write turn, run
`flow_index.py|js render --repo <repo>` to project that machine record into
`docs/flows/README.md`. Rendering is document writing and never precedes the
plan gate.

For GitNexus, export `Route`, `Process`, and `Community` properties through its
MCP/cypher interface. Processes are heuristic Entry-to-Terminal paths, not
business flows. Group them by `entryPointId`, retain the terminal set and
community crossing as reach evidence, and emit one candidate per entry.
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
application/service layer membership, tour context, and entry-like file/symbol
names. A knowledge graph containing only `contains` edges supplies structure,
not an ordered call flow.

Every row records a normalized `entry_ref`, evidence, confidence, reach, rank,
and one of `main`, `deferred`, `documented`, or `skipped`. Only `main` rows may
be added as dynamic `docs/flows/{slug}.md` documents. Deferred rows remain in
the index and are not placeholder documents.

## Derive main-flow detail

Use this procedure when a main row requires a flow document and the chosen
provider has a code graph but no native flow graph.

1. Run `derive_flow_graph prepare --repo <repo>`. It ranks externally visible
   entry points and emits a bounded analysis context.
2. Analyze main entries in rank order. Record actors, trigger, ordered steps,
   branches, rules, failures, and outcome.
3. Run `derive_flow_graph write --repo <repo> --analysis <analysis.json>`.
4. Treat `.docforge/tmp/flow-graph.json` as provisional. Confirm business rules
   against source before asserting them.
5. Rerun `precheck_graph --repo <repo> --need flow`.

Containment edges never establish execution order. The derived file is
temporary, git-ignored, and regenerated when needed. Native provider detail
takes precedence.

## Cross-repository use

`entry_ref` is the durable join surface for Portfolio analysis. Normalize HTTP
routes, queue/topic names, schedules, and CLI commands so an outbound boundary
in one member repository can match an inbound flow entry in another. Preserve
the original signatures in evidence; do not claim a cross-repository link from
name similarity alone.
