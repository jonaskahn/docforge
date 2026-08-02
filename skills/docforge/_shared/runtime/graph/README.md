# Graph runtime

Code-graph and flow-graph provider adapters, the shared storage layer they
read/write through, and the precondition checks every workflow calls before
analysis or writing. Public launchers live in
[`runtime/cli/`](../cli/README.md) — run `python3 runtime/cli/python/<name>.py`
or `node runtime/cli/js/<name>.js`, never the implementation files directly.

## Provider matrix

| Provider | Code graph | Flow graph | Read mode | Notes |
|---|---|---|---|---|
| Understand Anything | yes | yes | JSON | `.ua/knowledge-graph.json` / `.ua/domain-graph.json` |
| GitNexus | yes | yes | DB (Ladybug) | staleness warns, does not block |
| CodeGraph | yes | no | MCP | DB presence ≠ MCP wiring; no offline reader |

Registry priority: Understand Anything → GitNexus → CodeGraph.

## Load this when

- Checking whether a code or flow graph is ready → `precheck_graph`.
- Reading a specific provider's index → `graph_source_codegraph`,
  `graph_source_gitnexus` (`detect`), `graph_source_gitnexus_reader`
  (offline DB inventory), `graph_source_understand_anything` (library).
- Adding a fourth provider → `graph_source_registry` (dispatch),
  `graph_storage` (shared file/path helpers); see
  [`../../references/graph/adding-a-graph-source.md`](../../references/graph/adding-a-graph-source.md).
- Troubleshooting all providers at once → `diagnose_graphs`.
- Probing a compatible JSON graph (e.g. Understand Anything) →
  `read_graph` — it cannot read GitNexus or CodeGraph databases.

## Contents

- `graph_storage.py`/`.js` — shared path/file helpers used by every adapter.
- `graph_source_registry.py`/`.js` — provider dispatch and readiness ranking.
- `graph_source_codegraph.py`/`.js`, `graph_source_gitnexus.py`/`.js`,
  `graph_source_gitnexus_reader.py`/`.js`,
  `graph_source_understand_anything.py`/`.js` — one adapter per provider.
- `precheck_graph.py`/`.js` — the `--need code|flow` CLI.
- `diagnose_graphs.py`/`.js` — all-provider troubleshooting; never the default
  intake path.
- `read_graph.py`/`.js` — JSON code-graph inventory (`--summary`, `--modules`,
  `--layers`, `--deps`, `--boundaries`); default input is an upward search for
  `.ua/knowledge-graph.json`.

Side effects: all graph *probes* are read-only. `graph_storage` write helpers
(`write_flow_graph`, `ensure_tmp_dir_gitignored`) write `.docforge/tmp/`
artifacts and ignore files; flow derivation writes are owned by
[`../flows/`](../flows/README.md).

## Where invoked

| Script | Documented callers | Programmatic callers |
|---|---|---|
| `precheck_graph` | [`workflows/planning.md`](../../workflows/planning.md), [`workflows/tools.md`](../../workflows/tools.md), [`references/graph/graph-sources.md`](../../references/graph/graph-sources.md), [`references/graph/flow-derivation.md`](../../references/graph/flow-derivation.md), [`references/graph/adding-a-graph-source.md`](../../references/graph/adding-a-graph-source.md), [`content/agent-context/templates/agents-flow.md`](../../content/agent-context/templates/agents-flow.md) | `flows/derive_flow_graph` |
| `read_graph` | [`references/graph/graph-source-understand-anything.md`](../../references/graph/graph-source-understand-anything.md), [`references/graph/adding-a-graph-source.md`](../../references/graph/adding-a-graph-source.md), [`references/graph/graph-sources.md`](../../references/graph/graph-sources.md) | `flows/derive_flow_graph` |
| `diagnose_graphs` | [`workflows/intake.md`](../../workflows/intake.md) | — |
| `graph_source_gitnexus_reader` | [`references/graph/adding-a-graph-source.md`](../../references/graph/adding-a-graph-source.md) | `precheck_graph`, `diagnose_graphs` |
| `graph_source_registry`, `graph_storage`, `graph_source_understand_anything`, `graph_source_codegraph`, `graph_source_gitnexus` | — adapter contract only: [`references/graph/adding-a-graph-source.md`](../../references/graph/adding-a-graph-source.md) | `precheck_graph`, `diagnose_graphs`, `flows/derive_flow_graph` |

## Boundaries

Owns provider mechanics only. Provider selection *policy* (when to ask the
user, provider sufficiency) lives in `../../workflows/intake.md` and
`../../references/graph/graph-sources.md`, not here.
