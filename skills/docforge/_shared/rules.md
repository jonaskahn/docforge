# Shared rules

Always load with either skill entrypoint. Procedural detail lives under
[`workflows/`](workflows/README.md); this file is the always-on contract.

## Path anchoring

The skill entrypoint hands this cartridge's root relative to its own SKILL.md:
`./_shared` for `docforge`, `../docforge/_shared` for the thin entrypoints.
Locate the copy of the entrypoint that the host loaded, then resolve every
`./` and `../` reference inside cartridge files against that root, never the
session working directory — the target repository does not contain the
cartridge unless it is self-hosting it. Lookup order:

1. **Repo-local self-host** — if the working repo contains
   `skills/<entrypoint>/SKILL.md`, the cartridge is
   `<repo>/skills/docforge/_shared`.
2. **Plugin root** — a plugin install keeps the same layout:
   `<plugin-root>/skills/docforge/_shared`.
3. **Global skill dirs** — the running agent's own skill dir first, then the
   shared standard set: `~/.agents/skills/docforge/_shared`,
   `~/.claude/skills/docforge/_shared`,
   `~/.config/opencode/skills/docforge/_shared`, plus any other skill dir the
   running agent documents.

Use the repo-local copy when the working repo self-hosts it; otherwise the
global one. If no copy can be located, ask the user for the absolute cartridge
root before following any cartridge link.

## Session tool runtime

There is no runtime-precheck CLI. Once per Docforge session, the agent
detects `PATH` and locks **one** engine for every Docforge tool call:

1. `python3` (3.10+), else `python` (3.10+).
2. Else `node` (22+), else `bun`, else `deno`.
3. If none are available, stop and ask the user to install one family.

Do not switch engines mid-session. Prefer Python when both families work.
Detail: [`workflows/tools.md`](workflows/tools.md),
[`runtime/cli/README.md`](runtime/cli/README.md).

## Code-graph precondition

A code graph is required before any analysis or writing; run
`precheck_graph.{py,js} --need code`. A flow graph is required only when a
selected document lists `flow_graph` in `requires`; check with `--need flow`
before writing the first such document.

**Portfolio-collection exception, root only:** when the session's confirmed
tier is `portfolio`, the repository root's own `detect_profiles` evidence is
empty (no source of its own to graph — see `discover_child_repos.{py,js}`'s
`root_profile_evidence` field), and every included member already holds its
own graph-grounded Diligence-or-higher baseline (the Readiness gate in
[`references/portfolio.md`](references/portfolio.md)), the root's own
BLOCKED code-graph result is not a session-blocking failure — record it as
"no source of its own" and continue with the `docs-portfolio/` layer. This
never waives the precondition for a member repository, and never applies when
the root shows any profile evidence at all. Detail:
[`workflows/planning.md`](workflows/planning.md).

## Graph provider persistence

The graph provider is locked into `manifest["graph"]` once — automatically, by
`manage_manifest.{py,js} init` — and every sub-agent for the rest of the
session, including a spawned parallel writer, reads that lock instead of
re-detecting or re-asking. It is not re-selected mid-session without
`set-graph --force`. Detail:
[`references/graph/graph-sources.md`](references/graph/graph-sources.md)
"Session persistence", [`workflows/writing.md`](workflows/writing.md).

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
3. Write documents in catalog `write_order`. Independent documents may be
   written concurrently by spawned sub-agents under the parallel-execution
   contract ([`references/parallel-execution.md`](references/parallel-execution.md)):
   workers edit only their own artifact files, and every manifest mutation
   stays a serial orchestrator operation.
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
[`references/quality-bar.md`](references/quality-bar.md)). A **run** is
complete only when the whole-tree gate passes and — unless the invocation
included `--plan-only` or `--no-dashboard` — the dashboard has been started
and its URL reported in the final response
([`workflows/validation.md`](workflows/validation.md) §7).
