# Graph sources

This file owns capability dispatch, provider selection, setup, and refresh
policy. Generated documents name capabilities—not provider commands.

## Capabilities

- `code_graph`: structure, modules, layers, call/import edges. Universal.
- `flow_graph`: actors, triggers, ordered steps, branches, and outcomes.
  Required only by selected catalog documents that list it.

Resolve flow data native-first. If no provider exposes a native flow graph,
derive `.docforge/tmp/flow-graph.json` from the selected code graph using
`derive_flow_graph.{py,js}`. The result is explicitly provisional and business
rules must be confirmed against source.

## Provider dispatch

| Provider | Code graph | Native flow graph | Read mechanism |
|---|---:|---:|---|
| Understand Anything | yes | yes | JSON files through `read_graph` |
| GitNexus | yes | when processes are indexed | MCP query; optional offline reader |
| CodeGraph | yes | no | `codegraph_explore` MCP tool |

When several sources are ready, show all and ask which to read. Under
`--auto-accept`, choose the first ready provider in registry order and state the
choice.

## Side-effect authority

- Detection and reading are read-only and agent-run.
- Repository index build or refresh may be agent-run only after explicit user
  approval.
- Global install, MCP wiring, and any setup requiring an agent restart are
  user-run.
- `--auto-accept` never substitutes for these approvals.

## Provider commands

Provider-specific commands are intentionally confined here and to each provider
reference.

- Understand Anything: invoke the installed provider’s code analysis, then flow
  analysis. A first run may consume substantial tokens; disclose that before
  requesting approval.
- GitNexus: the user installs/wires it as needed; after approval, a repository
  index may be built or refreshed with `npx gitnexus analyze`.
- CodeGraph: the user performs global MCP setup with `codegraph install`; after
  approval, a repository index may be initialized with `codegraph init`.

After any build or refresh, rerun `precheck_graph --need code`; use
`--need flow` only before a selected flow-dependent document.

## Reading

Read graph facts narrowly for the active document:

- architecture: module/layer inventory, boundaries, and edge direction;
- setup/reference: manifests plus graph-discovered entry points;
- flows: native or provisional flow graph, then source confirmation;
- risks: graph hotspots plus manifests and history;
- decisions: graph structure cross-checked against git history.

The selected provider affects retrieval, not document language or contracts.
