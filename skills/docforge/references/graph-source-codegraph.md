# CodeGraph source

CodeGraph provides `code_graph` through `.codegraph/codegraph.db`. It does not
provide `flow_graph`; use native data from another ready provider or Docforge’s
provisional flow derivation.

Detection checks only that the index exists. Reading requires the
`codegraph_explore` MCP tool in the current session; never open the SQLite file
directly. If the index exists but the tool is unavailable, this source is not
readable in the session.

Global MCP wiring is user-run:

```sh
codegraph install
```

It requires an agent restart. Once CodeGraph is installed and the user has
explicitly approved repository index construction, the agent may run:

```sh
codegraph init
```

The file watcher maintains an initialized index; do not invent a refresh
command. `--auto-accept` does not supply build/install approval.

Query narrowly with `codegraph_explore`, naming the area, file, or symbol. Use
its source, call paths, and blast-radius output as evidence; generated
documentation still speaks only about the code-graph capability.
