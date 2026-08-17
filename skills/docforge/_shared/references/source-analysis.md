# Source analysis

Use the provider selected through `graph-sources.md`. This file owns the
provider-neutral evidence loop; provider references own the skill/MCP/CLI
commands.

## Evidence order

Use this bounded retrieval ladder:

1. Query the code graph for the current evidence question: boundaries, entry
   points, relevant symbols, source-bearing call paths, and dependency edges.
   For flow-dependent work, query only the applicable native or provisional
   flow portions. Stop when the returned paths and source answer the question.
2. Read the targeted symbols, regions, and source-bearing flow portions needed
   to confirm behavior. Stop when behavior, branches, and failures required by
   the document contract are supported.
3. Search for precise keywords only within the candidate file set returned by
   earlier steps. Expand that set only through discovered imports, calls,
   configuration references, or tests. Stop when every required claim has
   direct evidence or a clearly recorded gap.
4. Escalate to a whole file only when the graph is stale, the file is a
   semantic manifest, configuration file, or entry point, a branch or failure
   path remains unresolved, or the file is small: at most 200 lines or 16 KiB.
   Record which condition justified the escalation and stop after resolving
   it.
5. Read git history last, and only for rationale, chronology, ownership
   evidence, or release framing that current source cannot establish.

Do not read an entire directory, package, or repository into context for
convenience. Directory-wide context reads hide evidence gaps and defeat the
retrieval bounds. If the ladder still cannot establish a derivable fact,
record the gap rather than widening scope without a new evidence question.

Read manifests for commands, versions, configuration, and published surface.
Declared dependencies also confirm and augment the frameworks and shapes
`detect_profiles.{py,js}` proposed from the same manifests (see
[`../runtime/catalog/README.md`](../runtime/catalog/README.md)). Reconcile
existing
documentation as evidence, never as unquestioned truth.

Ask narrow capability questions. Retrieve the files and edges that answer the
current document contract rather than requesting a generic system summary.
Do this once for the planning inventory and again for each document’s narrower
evidence card. A ready index that is never queried does not ground a plan.

## Evidence by document family

| Family | Primary evidence |
|---|---|
| architecture | code graph, deployment/build manifests, narrow source confirmation |
| flows and flow-derived views | flow graph, entry-point paths, rule/failure confirmation |
| setup/testing/configuration | manifests, CI, environment reads, commands verified locally |
| dependencies/security/risks | manifests, code-graph edges, controls, history |
| decisions | history and the code structure that resulted |
| portfolio | child-repository discovery, member manifests, each member’s graph evidence |
| Business Analyst | native/provisional flows, source-confirmed rules, tests, connected requirement evidence |
| Product Owner | reachable capabilities, release history, instrumentation, stakeholder evidence |
| coding-agent context | entry points, representative paths, tests, constraints, hotspots |

Treat graph output as evidence to synthesize, not prose to paste. If evidence
cannot establish an external value, use one typed token. If evidence should
establish a fact but does not, query or inspect further; do not punt it.

Synthesize every source mention into a human-readable link, never a raw
path, `file:line` string, or symbol dump: `[<readable label> (<repo-relative
path>)](<repo-relative path>)` (see the source-references rule in
[`host-neutrality.md`](host-neutrality.md)).
