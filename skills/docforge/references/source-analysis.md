# Source analysis

Use the provider selected through `graph-sources.md`. This file owns the
provider-neutral evidence loop.

## Evidence order

1. Read the code graph for structure, boundaries, entry points, and dependency
   edges.
2. Read manifests for commands, versions, configuration, and published surface.
3. Read a native or provisional flow graph only for a selected document that
   requires `flow_graph`.
4. Inspect the narrow source paths needed to confirm behavior, edge cases, and
   failure handling.
5. Read git history for rationale, chronology, ownership evidence, and release
   framing.
6. Reconcile existing documentation as evidence, never as unquestioned truth.

Ask narrow capability questions. Retrieve the files and edges that answer the
current document contract rather than requesting a generic system summary.

## Evidence by document family

| Family | Primary evidence |
|---|---|
| architecture | code graph, deployment/build manifests, narrow source confirmation |
| flows and flow-derived views | flow graph, entry-point paths, rule/failure confirmation |
| setup/testing/configuration | manifests, CI, environment reads, commands verified locally |
| dependencies/security/risks | manifests, code-graph edges, controls, history |
| decisions | history and the code structure that resulted |
| portfolio | child-repository discovery, member manifests, each member’s graph evidence |

Treat graph output as evidence to synthesize, not prose to paste. If evidence
cannot establish an external value, use one typed token. If evidence should
establish a fact but does not, query or inspect further; do not punt it.
