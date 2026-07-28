# CodeGraph source

CodeGraph stores a local SQLite index at `.codegraph/codegraph.db`. It provides
`code_graph`: symbols, relationships, routes, relevant source, call paths, and
blast-radius context. It does not expose a native business `flow_graph`.

## Prepare

CLI installation and agent MCP wiring are user-run:

```sh
codegraph install
```

The agent must be restarted for newly wired MCP tools to appear. Once the tool
is available, repository index construction may be agent-run only after
explicit approval:

```sh
codegraph init
```

`init` creates `.codegraph/` and builds the graph. Detection of the SQLite file
does not prove the current agent session can query it; both the artifact and
`codegraph_explore` must be available.

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
area, file, or symbol and ask the complete relationship question in one call.
The response includes the relevant line-numbered source, call paths (including
resolved dynamic-dispatch hops where supported), and a blast-radius summary.

Useful Docforge queries include:

- “Show the request path from route X through persistence, with the relevant
  source and failure branches.”
- “Explain the modules and dependency direction in area Y; identify boundary
  crossings and high fan-in/out symbols.”
- “Locate configuration reads for feature Z and the tests exercising each
  branch.”
- “Find entry points for this worker/command and trace the downstream calls.”

Pass `projectPath` when querying a project other than the current indexed root
or an indexed service inside a monorepo. Treat returned source as read evidence;
follow a staleness warning by reading the named live file.

## Use in Docforge

- Plan architecture, API, web, library, and infrastructure documents directly
  from the returned nodes and relationships.
- Use framework-aware route nodes and call paths as candidates for dynamic
  flows.
- Derive a provisional flow graph through `flow-derivation.md` only if a
  selected document requires `flow_graph` and no native provider supplies it.
- Confirm business actors, rules, and outcomes from source or stakeholder
  evidence; a structural path alone is not a business process.

Never open or query `codegraph.db` directly. The MCP/CLI interface owns schema
and synchronization behavior.
