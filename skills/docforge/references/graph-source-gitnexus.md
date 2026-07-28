# GitNexus source

GitNexus stores its index at `.gitnexus/lbug`, with summary/staleness metadata
in `.gitnexus/meta.json`. It provides `code_graph` and may provide native
`flow_graph` through indexed processes.

Prefer the GitNexus MCP for read-only queries:

- repository context and schema resources for orientation;
- symbol context for callers, callees, and process membership;
- process resources for ordered flow steps;
- structural queries for narrow evidence questions.

The optional offline readers
`graph_source_gitnexus_reader.{py,js}` query the database in place. The Node
reader requires `@ladybugdb/core`; the Python reader requires a compatible
binding. This is the documented exception to the core no-dependency rule.

Global MCP setup is user-run and may require restart:

```sh
npx gitnexus setup
```

After explicit user approval, the agent may build or refresh the repository
index:

```sh
npx gitnexus analyze
```

`--auto-accept` never supplies this approval. Re-run graph precheck after a
build. Native process labels may be code-derived; preserve them unless source
evidence supports a clearer business name.
