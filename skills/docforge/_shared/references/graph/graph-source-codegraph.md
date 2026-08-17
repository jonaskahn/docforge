# CodeGraph source

CodeGraph stores a local SQLite index at `.codegraph/codegraph.db`. It
provides `code_graph`: symbols, relationships, routes, relevant source, call
paths, and blast-radius context. It does not expose a native business
`flow_graph`.

## Prepare

CLI installation and agent MCP wiring are user-run:

```sh
codegraph install
```

The agent must be restarted for newly wired MCP tools to appear. Once the
tool is available, repository index construction may be agent-run only after
explicit approval:

```sh
codegraph init
```

`init` creates `.codegraph/` and builds the graph. Detection of the SQLite
file does not prove the current agent session can query it; both the
artifact and `codegraph_explore` must be available.

CodeGraph normally watches changes and reconciles at MCP connection time.
Check exceptional environments with:

```sh
codegraph status
codegraph sync
```

Do not run manual sync as routine ceremony. Use it only when status reports
pending changes, the watcher is disabled, or a script needs a pre-flight
refresh. `--auto-accept` never supplies install or build approval.

## Query

Use `codegraph_explore` before grep/read for structural questions. Name the
area, file, or symbol and ask the complete relationship question in one
call. The response includes the relevant line-numbered source, call paths
(including resolved dynamic-dispatch hops where supported), and a
blast-radius summary.

Useful Docforge queries include:

- "Show the request path from route X through persistence, with the relevant
  source and failure branches."
- "Explain the modules and dependency direction in area Y; identify boundary
  crossings and high fan-in/out symbols."
- "Locate configuration reads for feature Z and the tests exercising each
  branch."
- "Find entry points for this worker/command and trace the downstream calls."

Pass `projectPath` when querying a project other than the current indexed
root or an indexed service inside a monorepo. Treat returned source as read
evidence; follow a staleness warning by reading the named live file.

## Use in Docforge

- Plan architecture, API, web, library, and infrastructure documents directly
  from the returned nodes and relationships.
- Use framework-aware route nodes and call paths as candidates for dynamic
  flows.
- Derive a provisional flow graph through `flow-derivation.md` only if a
  selected document requires `flow_graph` and no native provider supplies it.
  The reader below gives that derivation an ordered, located skeleton rather
  than a blank page.
- Confirm business actors, rules, and outcomes from source or stakeholder
  evidence; a structural path alone is not a business process.

## Structural reads

Never **write** to `codegraph.db`, and never treat it as a general query
surface — CodeGraph's own CLI and watcher own schema and synchronization.

Read-only structural queries go through
`graph_source_codegraph_reader.{py,js}`, which opens the file read-only and
refuses to read a `schema_versions` newer than it knows, falling back to the
MCP path:

```sh
python3 runtime/cli/python/graph_source_codegraph_reader.py entries --repo <repo> --limit 15
python3 runtime/cli/python/graph_source_codegraph_reader.py paths  --repo <repo> --seed <node-id>
```

`entries` ranks flow seeds — routes first (scored by what their handler
reaches, since a route node has no outgoing calls of its own), then exported
functions nothing calls, then call fan-out. `paths` walks ordered
entry→terminal chains, each hop carrying `file` and `line`. Both feed
`derive_flow_graph prepare` and `flow_index harvest`, which is what makes a
CodeGraph-only repository harvestable at all.

That split is the whole point: **the reader supplies structure, the MCP
supplies meaning.** Having walked a chain, use `codegraph_explore` on its
symbols to establish what the reader cannot — the branch conditions, the
business rules, the failure handling. Do not ask the reader for those, and do
not ask the MCP to re-derive the call order.

Two limits to expect. Method dispatch through a service object
(`contentService.getActivities()`) resolves to the object, so a chain may end
at a `constant` — continue by reading the file. And a self-recursive handler
yields a one-hop chain, not a deep one; that is the cycle guard being correct,
not a truncation.
