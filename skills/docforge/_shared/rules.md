# Shared rules

Always load with either skill entrypoint. Procedural detail lives under
[`workflows/`](workflows/README.md); this file is the always-on contract.

## Path anchoring

The skill entrypoint hands this cartridge's absolute root to the session
(`${CLAUDE_SKILL_DIR}/_shared` for `docforge`,
`${CLAUDE_SKILL_DIR}/../docforge/_shared` for the thin entrypoints; plugin
agents receive `${CLAUDE_PLUGIN_ROOT}/skills/docforge/_shared`). Resolve every
`./` and `../` reference inside cartridge files against that root, never the
session working directory — the target repository does not contain the
cartridge unless it is self-hosting it. If no absolute root was given, locate
the cartridge (repo-local `skills/docforge/_shared`, the plugin install, or a
global skill dir) before following any cartridge link, or ask the user.

## Session tool runtime

There is no runtime-precheck CLI. Once per Docforge session, the agent
detects `PATH` and locks **one** engine for every Docforge tool call:

1. `python3` (3.10+), else `python` (3.10+).
2. Else `node` (18+), else `bun`, else `deno`.
3. If none are available, stop and ask the user to install one family.

Do not switch engines mid-session. Prefer Python when both families work.
Detail: [`workflows/tools.md`](workflows/tools.md),
[`runtime/cli/README.md`](runtime/cli/README.md).

## Code-graph precondition

A code graph is required before any analysis or writing; run
`precheck_graph.{py,js} --need code`. A flow graph is required only when a
selected document lists `flow_graph` in `requires`; check with `--need flow`
before writing the first such document. Detail:
[`workflows/planning.md`](workflows/planning.md).

## Provider sufficiency rule

One readable `code_graph` is enough. Understand Anything, GitNexus, and
CodeGraph are equally trusted when READY; missing competing providers are
normal and must never appear in an intake, plan summary, or readiness table.
One ready provider is the proposed default; several ready providers are
offered as a choice; no ready provider gets an explained setup path. Do not
invent dual native-flow claims (for example “Understand Anything + GitNexus”)
unless both were READY and the user chose a primary. Detail:
[`workflows/intake.md`](workflows/intake.md),
[`references/graph/graph-sources.md`](references/graph/graph-sources.md).

## Safety boundaries

1. Do not invent. Derive every fact from a graph, source, manifest, history,
   existing documentation, or user-provided evidence. Reserve typed
   `<UPPER_SNAKE_CASE>` tokens for atomic external values only.
2. Build and show the plan before writing. `--auto-accept` waives routine
   conversational pauses; see [`flags.md`](flags.md) for the explicit list of
   excluded side effects and mandatory safety gates.
3. Write one document at a time, in catalog `write_order`.
4. Stamp provenance while writing (YAML provenance 2.0, byte one). Replace
   every scaffold token with concrete write metadata and source blobs.
5. A writer never marks its own artifact complete; mechanical lint is
   necessary but never sufficient.
6. State a fact once in its owning document; link to it elsewhere.
7. Generated prose stays provider-neutral and host-neutral.

## Completion requirement

A document reaches `complete` only after mechanical lint and an independent,
artifact-only audit pass ([`workflows/writing.md`](workflows/writing.md)),
and the whole tree passes `scaffold_docs --audit` plus the cross-document
quality gate ([`workflows/validation.md`](workflows/validation.md),
[`references/quality-bar.md`](references/quality-bar.md)).
