# Intake

Owns: bare `/docforge` invocation, safe discovery, profile detection, the
discovery gate, scope questions, the confirmation gate, and graph-provider
choice.

## Bare `/docforge` invocation

When the user invokes `/docforge` with no task, flags, tier, or typed profile
document request, begin an **interactive intake**. Do not initialize a
manifest, scaffold a file, build/refresh a graph, install a provider, change
configuration, or archive/delete anything.

First perform only safe discovery: identify the repository root, check whether
`.docforge/manifest.json` exists, run the read-only code-graph precheck, and run
`detect_profiles` to identify candidate shapes, platforms, frameworks, and
concerns. `detect_profiles` recognizes frameworks and shapes by reading
*declared dependencies* structurally from project-definition manifests
(`package.json`, `pyproject.toml`/`requirements.txt`, `pom.xml`,
`build.gradle*`, `go.mod`, `Cargo.toml`, `Gemfile`, `composer.json`,
`*.csproj`, `pubspec.yaml`), not by substring — so a declared dependency is
**strong** evidence. Path fragments and content keywords are **weak** cues:
they never alone confirm a profile. The same noun or team term can mean
different aspects across projects, stacks, and domain language.

When the pack from `detect_profiles --emit-gate-pack` sets `needs_gate`, run the
**discovery gate** before presenting profile choices: follow
[`../references/discovery-gate.md`](../references/discovery-gate.md), ground
decisions only in the bounded pack, and emit judgment JSON (`promote` / `keep`
/ `demote` / `drop` / `propose`). Apply it with `discovery_gate` helpers; on
invalid judgment, fail open to deterministic ranks. Present **recommended**
vs **also possible** with evidence and gate reasons. Detection and the gate
propose profiles; they never confirm them on the user's behalf. When exactly
one readable code-graph provider is ready, use it as the proposed default and
do not ask the user to choose among absent providers. This read-only provider
selection is not permission to build, refresh, install, or configure
anything.

## Scope intake

Present all applicable unresolved questions together in one intake. Explain in
plain language why each question matters, then give every choice a short
consequence so the user can select one answer per question (or multiple answers
where explicitly allowed). Use native single-select and multi-select controls
when the host provides them; otherwise use a concise numbered question set with
lettered options. Do not prescribe an exact screen or require a particular
combined answer syntax.

Ask only what remains unresolved, in this order:

1. **Goal or action.** For a repository without a manifest, offer creating a
   new documentation plan or planning without writing. When a manifest exists,
   also offer resuming it, checking status or staleness, revising a named area,
   revising flows, or replacing the plan. Briefly distinguish inspection,
   planning, writing, and read-only reporting.
2. **Documentation tier.** For a new or plan-only scope, offer Spine
   (essential repository documentation), Diligence (Spine plus flows, risks,
   security, operations, dependencies, and ADRs), Portfolio (Diligence plus
   `docs-portfolio/` diligence views), or a grounded recommendation that
   Docforge will explain after inspection.
3. **Repository profiles.** After detect (and the discovery gate when
   `needs_gate`), show ranked multi-aspect recommendations with evidence, then
   let the user confirm or edit each applicable dimension:
   - shapes describe what the repository delivers;
   - platforms describe where it runs;
   - frameworks describe how it is built and tailor evidence queries without
     adding framework-specific trees;
   - concerns describe evidenced cross-cutting behavior;
   - audiences describe whom the documentation serves.
   Permit multiple values in every dimension — one overloaded cue may map to
   several aspects when evidence supports it. Offer Engineers + beginners as
   the default audience starting point (and the manifest CLI default when no
   audience flag is supplied); BA + PO, coding agents, operators, and security
   reviewers add their catalog-owned views.
4. **Graph source, only when unresolved.** With several ready providers, offer
   only those providers. With no ready provider, explain setup paths and their
   approval requirements. With exactly one ready provider, record it as the
   proposed source and skip this question; include it in the final confirmation
   so the user can still ask to compare or change it.
5. **Execution mode.** Offer Review (pause after every new or changed tree),
   Auto-accept (always display trees and updates, then continue without routine
   conversational pauses), or Plan only (stop after the completed tree and
   document cards). Explain that Auto-accept never approves installation,
   configuration, indexing, refreshes, or destructive work.

Collect the applicable answers as one response. If the user supplied one or
more choices in the original request, retain them and include only unresolved
questions in the intake. For Resume, Status, Revise, or Revise flow, omit tier,
audience, and shape questions that the existing manifest already resolves. If
the reply leaves a material choice missing or ambiguous, ask one concise
follow-up containing only those unresolved choices.

After resolving the answers, display one confirmation summary containing the
action, tier, every selected profile dimension, selected graph provider and its
code/flow capabilities, and execution mode. Ask whether to continue, edit a
choice, or cancel. Always wait for explicit confirmation of this intake
summary, including when Auto-accept was selected. Only after confirmation may
Docforge initialize or replace a manifest or begin deeper planning. Later
plan-tree pauses follow the selected execution mode.

Show only currently valid choices. Do not offer Resume, Status, Revise, or
Revise flow when no manifest exists, and do not present a provider that needs
setup as ready. If no code graph is ready, explain that global
installation/MCP wiring is user-run and that an agent-run repository index
build or refresh needs separate explicit approval; selecting a setup path is
not that approval. If a manifest exists, include its tier, typed profiles, and
incomplete count in the first explanation.
Report existing documentation and candidate repository shapes with a brief
evidence note, such as an API schema, web framework manifest, library package
manifest, pipeline configuration, or infrastructure files.

## Provider sufficiency rule, in detail

Docforge needs one readable `code_graph`, not one index from every supported
provider. Missing competitors are normal and must not appear in the standard
intake, plan summary, or readiness table.

- One ready provider: state it once and proceed with it as the proposed
  default.
- Several ready providers: list only those ready providers and ask which should
  be primary.
- No ready provider: explain the available setup paths and ask the user to
  choose one.
- Selected flow-dependent documents: first use the chosen provider's native
  flow capability; derive provisionally only when it has none.

For example, `.gitnexus/lbug` with indexed Process nodes satisfies both
`code_graph` and native `flow_graph`. Do not mention absent Understand Anything
or CodeGraph indexes in that case unless the user asks to compare or switch.
The all-provider output of `diagnose_graphs` is troubleshooting detail and is
never the default `/docforge` intake.

Explicit requests such as "create diligence API documentation" skip answered
questions; present any materially missing scope questions together. The final
intake confirmation and all side-effect approvals remain mandatory under
`--auto-accept`.

## Invocation flags relevant to intake

- `--plan-only`: precheck, analyze, initialize the complete static manifest,
  add discovered dynamic documents, and display the dry-run tree. Do not create
  placeholder documents.
- `--auto-accept`: display each plan and result but continue without
  conversational confirmation pauses. It never authorizes installation, global
  configuration, graph construction or refresh, archive/delete actions, or any
  other separately approved side effect.

An explicit single-document request still requires graph precheck, re-grounding,
mechanical lint, independent audit, and manifest state updates.

Next: once scope is confirmed, proceed to
[`planning.md`](planning.md).
