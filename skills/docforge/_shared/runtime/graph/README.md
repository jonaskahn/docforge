# Graph runtime

Code-graph and flow-graph provider adapters, the shared storage layer they
read/write through, and the precondition checks every workflow calls before
analysis or writing.

## Load this when

- Checking whether a code or flow graph is ready → `precheck_graph`.
- Adding a fourth provider → `graph_source_registry` (dispatch),
  `graph_storage` (shared file/path helpers); see
  [`../../references/graph/adding-a-graph-source.md`](../../references/graph/adding-a-graph-source.md).
- Reading a specific provider's index → `graph_source_codegraph`,
  `graph_source_gitnexus` (+ `graph_source_gitnexus_reader` for the
  deterministic JSON reader), `graph_source_understand_anything`.
- Troubleshooting all providers at once → `diagnose_graphs`,
  `read_graph`.

## Contents

- `graph_storage.py`/`.js` — shared path/file helpers used by every adapter.
- `graph_source_registry.py`/`.js` — provider dispatch and readiness ranking.
- `graph_source_codegraph.py`/`.js`, `graph_source_gitnexus.py`/`.js`,
  `graph_source_gitnexus_reader.py`/`.js`,
  `graph_source_understand_anything.py`/`.js` — one adapter per provider.
- `precheck_graph.py`/`.js` — the `--need code|flow` CLI.
- `diagnose_graphs.py`/`.js`, `read_graph.py`/`.js` — all-provider
  troubleshooting output; never the default intake path.

## Boundaries

Owns provider mechanics only. Provider selection *policy* (when to ask the
user, provider sufficiency) lives in `../../workflows/intake.md` and
`../../references/graph/graph-sources.md`, not here.
