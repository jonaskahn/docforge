# GitNexus source

GitNexus persists a property graph in `.gitnexus/lbug` and index metadata in
`.gitnexus/gitnexus.json` or legacy `.gitnexus/meta.json`. Its ingestion
pipeline precomputes calls, dependencies, communities, and execution
processes. That makes it useful for both `code_graph` and, when Process nodes
exist, native `flow_graph`.

## Prepare

Global/editor MCP setup is user-run because it changes agent configuration:

```sh
npx gitnexus setup
```

From the repository root, index construction or refresh may be agent-run only
after explicit approval:

```sh
npx gitnexus analyze
```

The command can also generate or update agent context files and hooks;
disclose those effects before requesting approval. A project-local
`.gitnexus/run.cjs` may be used for later commands when GitNexus generated it.
`--auto-accept` never supplies index-build approval.

GitNexus queries the last completed index. Compare its indexed commit with
`HEAD`; refresh after material changes. Do not run an index writer while the
MCP server or another process holds the embedded database.

## Query

Prefer the installed GitNexus skill and MCP server. Start by listing indexed
repositories and pass the repository identifier explicitly when more than one
is registered.

Use narrow native operations:

- `query`: find a concept, functional area, or process;
- `context`: inspect a symbol's callers, callees, references, and process
  participation;
- `impact`: measure upstream/downstream blast radius and risk;
- `trace`: find a directed path between two symbols;
- `detect_changes`: relate a diff to affected symbols and processes;
- `route_map`, `tool_map`, or `api_impact`: ground applicable profile plans;
- `cypher`: answer a precise structural question not covered by a
  higher-level tool.

Repository context and schema resources are useful for orientation. Process
resources or Process nodes provide ordered flow evidence; Community nodes are
functional clusters, not automatically business domains.

CLI equivalents are available when MCP is unavailable:

```sh
node .gitnexus/run.cjs query "authentication flow" --repo <repo>
node .gitnexus/run.cjs context <symbol> --repo <repo>
node .gitnexus/run.cjs impact <symbol> --direction upstream --repo <repo>
node .gitnexus/run.cjs cypher "<read-only query>" --repo <repo>
```

The optional `graph_source_gitnexus_reader.{py,js}` tools inventory
`.gitnexus/lbug` in place. The Node reader requires `@ladybugdb/core`; the
Python peer requires a compatible LadybugDB binding. This is a fallback for
read-only inventory, not a replacement for GitNexus's richer MCP responses.

## Use in Docforge

- Architecture: query communities, high-connectivity symbols, and
  representative call paths.
- Flow index: enumerate Routes and Processes, group Processes by
  `entryPointId`, preserve terminal/community reach, and rank one candidate
  per entry. Add manifest documents only for main rows; a Process node is not
  automatically a business flow.
- BA views: translate process steps into business language and confirm every
  decision rule in source.
- PO views: connect shipped entry points and releases to features; never
  derive product value from cluster names.
- Agent views: surface entry points, change blast radius, tests, and
  recurring patterns without pasting graph internals.

Preserve graph labels as evidence, but use a clearer business name only when
source, existing docs, or stakeholder evidence supports it.
