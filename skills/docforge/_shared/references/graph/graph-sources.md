# Graph sources

This file owns graph preparation, provider selection, native query dispatch,
setup, and refresh policy. Docforge does not replace a provider’s index with a
weaker directory scan. It detects and reuses the provider’s persisted graph,
then uses the provider’s own skill, MCP server, CLI, or read-only JSON reader
to answer narrow evidence questions.

Generated documents remain provider-neutral: they name repository facts and
the capabilities used to establish them, never the command used to retrieve
them.

## Capabilities

- `code_graph`: structure, symbols, modules, layers, calls, imports, and
  dependency edges. This is universal.
- `flow_graph`: actors, triggers, ordered business steps, decisions, and
  outcomes. This is required only by selected catalog documents that list it.

A provider index is prepared before document synthesis, not copied into the
documentation tree. The manifest records which documents need which
capabilities; provenance records the repository sources used for claims.

## Provider-native lifecycle

| Provider | Persisted artifact | Native strengths | Native read path | Refresh behavior |
|---|---|---|---|---|
| Understand Anything | `.ua/knowledge-graph.json` and `.ua/domain-graph.json` (legacy `.understand-anything/`) | shareable code-graph JSON; semantic summaries; native flows and steps | Understand Anything skills for exploration; `read_graph.{py,js}` for deterministic JSON inventory (see [`../../runtime/graph/README.md`](../../runtime/graph/README.md)) | `/understand` is incremental; optional auto-update hook |
| GitNexus | `.gitnexus/lbug` plus index metadata | calls, dependencies, communities, indexed execution processes, change/impact views | GitNexus MCP tools/resources or project-local CLI; optional read-only LadybugDB inventory | `analyze` refreshes the index; compare indexed commit with `HEAD` |
| CodeGraph | `.codegraph/codegraph.db` | current source, symbol relationships, call paths, routes, and blast radius in one query | `codegraph_explore` MCP tool (or its CLI equivalent when the skill directs it) | watcher and connect-time reconciliation; `status`/`sync` for exceptional manual checks |

The dedicated references contain the exact provider commands and query
recipes:

- [`graph-source-understand-anything.md`](graph-source-understand-anything.md)
- [`graph-source-gitnexus.md`](graph-source-gitnexus.md)
- [`graph-source-codegraph.md`](graph-source-codegraph.md)

When those provider capabilities are installed, dispatch through their native
agent surfaces instead of reconstructing the same query with filesystem tools:

| Need | Understand Anything | GitNexus | CodeGraph |
|---|---|---|---|
| build/update structure | `understand` skill | `gitnexus-cli` skill (`analyze`) | approved `codegraph init`; watcher thereafter |
| architecture/how it works | `understand-chat` or `understand-explain` | `gitnexus-exploring` | `codegraph_explore` |
| flows | `understand-domain` | process resources through `gitnexus-exploring` | provisional derivation from structural paths |
| change/blast radius | `understand-diff` | `gitnexus-impact-analysis` / `detect_changes` | `codegraph_explore` blast-radius output |

Skill invocation spelling is host-specific. On Codex, Understand Anything uses
the installed `$understand*` skills; on slash-command hosts it uses
`/understand*`. GitNexus skills call its MCP tools/resources according to their
own contract.

## Selection

Run `precheck_graph.{py,js} --need code` (see
[`../../runtime/graph/README.md`](../../runtime/graph/README.md)). One readable
provider is sufficient; Docforge
does not require or benefit from building every supported provider index.

- If exactly one source is ready, select it as the proposed default and report
  only that source, its artifact, capabilities, and read mechanism.
- If several sources are ready, present only those ready sources and ask which
  should be primary.
- If none are ready, present setup paths for the providers that could satisfy
  the missing capability.

An absent provider is not a readiness gap when another source already supplies
`code_graph`. Do not show “not detected,” “not indexed,” or “needs build” rows
for unused competitors in the standard intake or plan. Show them only for an
explicit compare/switch request or all-provider diagnostics.

- Prefer Understand Anything when its shareable JSON or native domain/flow
  graph is the main advantage.
- Prefer GitNexus when execution processes, communities, change impact, or
  cross-symbol traces are the dominant evidence need.
- Prefer CodeGraph when fast, current structural exploration with returned
  source and call paths is the dominant need.

If several are ready, use unselected ready sources as corroboration only when
useful. Under `--auto-accept`, select the first ready provider in registry
order, state the choice, and continue. Never merge incompatible provider
schemas into a synthetic “master graph.”

GitNexus with a readable `.gitnexus/lbug` and indexed Process nodes supplies
both `code_graph` and native `flow_graph`; neither Understand Anything nor
CodeGraph needs to exist for Docforge to plan and write documents. CodeGraph
with a readable `.codegraph/codegraph.db` (and a session-wired
`codegraph_explore`) is equally sufficient for `code_graph`; absent Understand
Anything or GitNexus indexes must not appear in that plan. Do not invent a
combined “Understand Anything + GitNexus” readiness claim unless both were
actually READY and the user selected a primary.

## Preparation and authority

Detection, readiness checks, status checks, and queries are read-only and may
be agent-run. Side effects remain deliberately separate:

- repository index build or refresh may be agent-run only after explicit user
  approval;
- global install, MCP configuration, plugin/skill installation, and
  restart-requiring setup are user-run;
- provider commands that generate `AGENTS.md`, `CLAUDE.md`, hooks, or other
  repository files must be disclosed before approval;
- `--auto-accept` never supplies approval for any of these actions.

After a build or refresh, rerun `precheck_graph.{py,js} --need code`. Do not
require a
flow graph yet unless the active manifest contains a selected document whose
`requires` includes `flow_graph`.

## Query before planning

Use the selected provider’s native interface to collect a planning inventory:

1. repository/module boundaries and deployable or published units;
2. entry points, routes, jobs, commands, and public interfaces;
3. main dependencies and cross-layer call paths;
4. candidate functional areas and flows;
5. hotspots, tests, configuration reads, and operational surfaces.

Then inspect manifests, current docs, and history. This evidence determines the
tier, profiles, conditions, and dynamic entries in the manifest. The plan is
therefore graph-grounded rather than a generic tier skeleton.

For each document, make another narrow provider-native query for its contract.
Examples:

- architecture: boundaries, representative symbols, layer edges, and paths;
- process/flow views: native process steps or provisional flow candidates,
  then source confirmation of decisions and failures;
- setup/configuration: graph entry points plus manifests and environment reads;
- risks: high fan-in/out paths, hotspots, dependency boundaries, and history;
- agent context: the smallest source-backed routes, patterns, tests, and
  constraints an editing agent needs.

## Flow resolution

Resolve flow data native-first. The numbered list below is a **fallback
order**, not a readiness claim for the plan summary — report only providers
that `precheck_graph.{py,js}` marked READY, and never echo “Understand
Anything +
GitNexus” when one or both are absent:

1. use Understand Anything’s native flow graph when ready;
2. use GitNexus indexed processes when ready;
3. otherwise derive `.docforge/tmp/flow-graph.json` from the selected code graph
   through [`flow-derivation.md`](flow-derivation.md).

CodeGraph is first-class for `code_graph` and an excellent derivation input,
but it has no native `flow_graph`. When CodeGraph is the only ready code graph
(or the selected primary has no native flow capability), the Capability
Schedule must say **Docforge-derived (provisional)**, never “Native flow
source: CodeGraph”.

Before choosing flow documents, harvest the complete
`.docforge/flow-index.json` through `flow_index.{py,js}` (see
[`../../runtime/flows/README.md`](../../runtime/flows/README.md)). GitNexus
Process nodes
are grouped by `entryPointId`; they are candidate path evidence, not one
document each. Understand Anything native flow nodes are confirmed entries,
then its knowledge graph is scanned for additional candidates because a domain
graph may cover only the main flows. The rendered `docs/flows/README.md`
matrix retains main and deferred candidates; only main entries become dynamic
flow documents.

The derived result is explicitly provisional. Confirm business rules and
failure behavior against source before publishing them. Containment edges do
not establish execution order. CodeGraph can provide excellent structural
paths, routes, and source for derivation, but Docforge does not relabel that
code graph as a native business flow graph.
