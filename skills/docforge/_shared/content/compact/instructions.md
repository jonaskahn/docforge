# Compact writing craft

Writing-craft instructions for compact-layout documents. Routes:

- `agents_compact` → [Writing the compact coding-agent reference](#writing-the-compact-coding-agent-reference)
- `architecture_compact` → [Writing `docs/architecture.md`](#writing-docsarchitecturemd)
- `ba_compact` → [Writing `docs/business-analyst.md`](#writing-docsbusiness-analystmd)
- `concepts_compact` → [Writing `docs/concepts.md`](#writing-docsconceptsmd)
- `contributing_compact` → [Writing `docs/contributing.md`](#writing-docscontributingmd)
- `decisions_compact` → [Writing `docs/decisions.md`](#writing-docsdecisionsmd)
- `engineering_compact` → [Writing `docs/engineering.md`](#writing-docsengineeringmd)
- `flows_compact` → [Writing `docs/flows.md`](#writing-docsflowsmd)
- `operations_compact` → [Writing `docs/operations.md`](#writing-docsoperationsmd)
- `po_compact` → [Writing `docs/product-owner.md`](#writing-docsproduct-ownermd)
- `product_compact` → [Writing `docs/product.md`](#writing-docsproductmd)
- `reference_compact` → [Writing `docs/reference.md`](#writing-docsreferencemd)
- `security_compact` → [Writing `docs/security.md`](#writing-docssecuritymd)

## Shared rules

- Ground each section from the repository evidence cited in provenance — one
  provenance `sections[]` entry per `##` heading.
- **Route to any spilled sibling.** A group that reached `COMPACT_SECTION_CAP`
  keeps its overflow at its own standard paths with no `README.md` above them —
  if this file does not link them, nothing does. Link every selected,
  materialized document in this section's folder that is not one of this file's
  `compact_members`, in `## Scope and boundaries`. Routing links are not
  sections: they do not violate the rule above, and `scaffold_docs --audit`
  fails the document when one is missing. Sections below name the folder where
  it is not "this section's folder". The coding-agent reference never links
  (agent-context isolation).
- **Profile-driven sections follow the core** — applies to `docs/architecture.md`,
  `docs/contributing.md`, `docs/engineering.md`, `docs/operations.md`,
  `docs/product.md`, `docs/reference.md`, `docs/security.md`: every document
  this project's confirmed profiles and audiences select for this section
  folds in here too, as its own `##` after the members listed above, in
  `compact_order`. Write each from its own member contract, at its own depth —
  a folded profile document is that document hosted in a shared file, not a
  summary of it. The manifest's `compact_members` is the authority on which
  ones this project has.

## Writing the compact coding-agent reference

Write one `##` section per topic member selected by the manifest, in this
order:

1. `## Architecture`: components, entry points, dependency direction, and
   boundaries.
2. `## Patterns`: repeated implementation shapes, representative source paths,
   hotspots, and applicable checks.
3. `## Testing`: exact commands, suite layout, selection, fixtures, isolation,
   and success signals.
4. `## Conventions`: evidenced safety, naming, structural, and workflow rules.
5. `## Tech debt`: observed limitations, editing risks, and safe handling.
6. `## Flows`: evidenced triggers, entry paths, durable sequences, results, and
   failure behavior.
7. `## Terms`: concise definitions, code context, and important distinctions.

Omit Conventions when its source condition is false. Omit Flows and Terms when
flow evidence is unavailable. Do not emit empty conditional sections.

Each selected section must answer its reader question without relying on any
other documentation. Facts may repeat between sections. Emit no Markdown
links, URLs, imports, references to peer outputs or human documentation, bare
generated-document paths, reader directions, or attribution language. Source
and configuration paths and verified commands are allowed.

Keep each selected section to roughly 25 lines. Prefer durable paths and stable
behavior over volatile symbols. Ground every heading in its own provenance
section, and never invent detail to fill the budget.

## Writing `docs/architecture.md`

The compact architecture file. Write one `##` section per member the
manifest actually selected, in this reading order, grounding each section
from the evidence its member contract requires. The first two sections exist
at every tier; the rest exist only when the project is compact **and**
Diligence or higher.

1. `## At a glance` — folder-index orientation (system mental model).
2. `## High-level architecture` — `architecture-high-level` (structure,
   boundaries, integration surfaces).
3. `## Component design` — `architecture-low-level` (selected whitebox
   decompositions, component responsibility/technology/public
   contract/directional relationships, one intra-block runtime scenario with
   its error path). Do not repeat the high-level map; go one level deeper
   only where the decomposition changes a reader's judgment.
4. `## Constraints` — `constraints` (hard bounds with source and design
   implication; deliberate non-goals). Keep temporary shortcuts and
   user-visible limitations out — those are owned elsewhere.
5. `## Dependencies` — `dependencies-inventory` (direct
   dependencies/integrations, purpose, criticality, failure behavior).
6. `## Technical debt` — `tech-debt-register` (shortcut, consequence,
   evidence, remediation direction). Keep hard constraints out — those belong
   in `## Constraints` above.

Do not add sections beyond what the manifest's `compact_members` for this
document actually lists, and do not route readers into source files.

## Writing `docs/business-analyst.md`

The compact business-analyst file. It replaces
`docs/product/business-analyst/README.md` and its three children.

Write one `##` section per member the manifest actually selected, in
`compact_order`, grounding each section from the evidence its member contract
requires:

1. `## At a glance` — business-analyst orientation: which business processes
   this system automates and where the rules live.
2. `## Process flows` — `process-flows` (actor, trigger, business-language
   steps, decision points, exceptions, outcome, owning flow links).
3. `## Business rules` — `business-rules` (stable rule id, plain-language
   statement, trigger, outcome, exceptions, enforcement evidence).
4. `## Requirements traceability` — `requirements-traceability` (requirement
   evidence, owning rule/flow, implementation, test, status).

Write in business language throughout. A reader who does not read code must be
able to follow every section; where a rule is enforced in code, cite the
evidence rather than reproducing the call chain.

State a rule once, in `## Business rules`, and link to it from the process
flow that applies it. Do not restate a rule inside a flow step.

Do not add sections beyond what the manifest's `compact_members` for this
document actually lists. Spilled siblings live in `docs/product/business-analyst/`.

## Writing `docs/concepts.md`

The compact concepts file. It replaces both
`docs/architecture/concepts/README.md` and the per-concept
`docs/architecture/concepts/{slug}.md` files a standard tree would
materialize.

Write the sections in this order:

1. `## At a glance` — the domain vocabulary this system is built on and which
   concepts a reader must hold to follow the architecture section.
2. `## Concept register` — every discovered concept: its name, where it is
   defined in the repository, and which documents depend on it. Give each row
   with a section below an anchor link to it; mark every other row
   `register only`.
3. One `##` section per concept the manifest recorded in `compact_members`, in
   `compact_order`. Write each from the `concept` contract at full depth.

**The register is the vocabulary; the sections are the budget.** The manifest
carries at most six concept sections
(`query_catalog.COMPACT_DYNAMIC_CAP`). A register-only concept is still named
and located in the code; it is never explained as though its lifecycle and
invariants had been analyzed.

A concept belongs here only when the repository defines it. A term that needs
one sentence is a glossary entry in `docs/reference.md`, not a section here.

Spilled siblings live in `docs/architecture/concepts/`.

## Writing `docs/contributing.md`

The compact contributing file. Exists only at Diligence or higher
(contributing content has no Spine members). Write one `##` section per
member the manifest selected, in this reading order, grounding each section
from the evidence its member contract requires:

1. `## At a glance` — folder-index orientation (how this section guides
   contributors). Link to the root `CONTRIBUTING.md` for the verified
   contribution path and required checks — that file stays separate and is
   never folded in here.
2. `## Ownership` — `ownership` (owned areas, responsibility boundaries,
   escalation tokens). Never invent people or teams the repository does not
   evidence.

Do not add sections beyond what the manifest's `compact_members` for this
document actually lists, and do not route readers into source files.

## Writing `docs/decisions.md`

The compact decisions file. It replaces both
`docs/architecture/decisions/README.md` and the per-decision
`docs/architecture/decisions/{slug}.md` files a standard tree would
materialize.

Write the sections in this order:

1. `## At a glance` — what kinds of decision this repository records and how a
   reader should use them.
2. `## Decision register` — every decision the repository evidences:
   identifier, title, status, date, and superseding record where one exists.
   Give each row with a section below an anchor link to it; mark every other
   row `register only`.
3. One `##` section per decision the manifest recorded in `compact_members`,
   in `compact_order`. Write each from the `adr` contract at its normal depth
   — a folded decision is a decision record hosted in a shared file, not a
   summary of one.

**The register is the record; the sections are the budget.** The manifest
carries at most six decision sections
(`query_catalog.COMPACT_DYNAMIC_CAP`). A decision that stays a register row is
still named, dated, and status-tracked; it is never written up as though its
context and alternatives had been analyzed. Never drop a row to make room for
a section, and never add a section the manifest does not list.

Decision evidence is commit history, migration files, configuration changes,
and code structure; see
[`../../references/decision-records.md`](../../references/decision-records.md).

Spilled siblings live in `docs/architecture/decisions/`.

## Writing `docs/engineering.md`

The compact engineering file. Write one `##` section per member the
manifest actually selected, in this reading order, grounding each section
from the evidence its member contract requires. The first three sections
exist at every tier; the rest exist only when the project is compact **and**
Diligence or higher — `## Conventions` additionally exists only when a
conventions source was found (same condition as the standard `conventions`
document).

1. `## At a glance` — folder-index orientation (how this repository is built
   and tested).
2. `## Setup` — `setup-guide` (getting a working checkout).
3. `## Testing` — `testing-guide` (how to run and extend the test suite).
4. `## Conventions` — `conventions` (evidenced style, structure, error
   handling, testing, and review conventions). Order dimensions by how often
   a contributor collides with them; drop any dimension the repository
   doesn't evidence.
5. `## Release` — `release-guide` (prerequisites, versioning, build,
   verification, publication, rollback).

Do not add sections beyond what the manifest's `compact_members` for this
document actually lists, and do not route readers into source files.

## Writing `docs/flows.md`

The compact flows file. It replaces both `docs/flows/README.md` and the
per-flow `docs/flows/{slug}.md` files a standard tree would materialize.

Write the sections in this order:

1. `## At a glance` — what kinds of work this system performs end to end, and
   which flows a reader should follow first.
2. `## Flow candidate matrix` — the complete matrix from
   `.docforge/flow-index.json`: every candidate, its normalized entry
   reference, area, confidence, reach, priority, and status. Give each row
   with a section below an anchor link to it (`[Checkout](#checkout)`), and
   mark every other row `matrix only` in its status column.
3. One `##` section per flow the manifest recorded in `compact_members`, in
   `compact_order`. Write each from the `flow` contract at full deep-dive
   depth — a folded flow is a flow document hosted in a shared file, not a
   summary of one.

**The matrix is the coverage statement; the sections are the budget.** The
manifest carries at most six flow sections
(`query_catalog.COMPACT_DYNAMIC_CAP`). Deferred candidates stay matrix rows
and are never written up as though they had been analyzed. Never drop a
candidate from the matrix to make room for a section, and never add a section
the manifest does not list — `manage_manifest add --type flow` decides which
flows fold, and it refuses past the budget.

Spilled siblings live in `docs/flows/`.

## Writing `docs/operations.md`

The compact operations file. Exists only at Diligence or higher (operations
content has no Spine members). Write one `##` section per member the
manifest selected, in this reading order, grounding each section from the
evidence its member contract requires:

1. `## At a glance` — folder-index orientation (deployment, observability,
   and operational boundaries).
2. `## Deployment` — `deployment` (environments, artifact path, rollout,
   rollback, verification). Keep incident procedures out.
3. `## Observability` — `observability` (signals, ownership, correlation,
   alert intent, blind spots). Keep provider marketing out.
4. `## Runbook index` — the complete runbook register: every discovered
   runbook, what it recovers, and its trigger. Give each row with a section
   below an anchor link; mark every other row `register only`.
5. One `##` section per runbook the manifest recorded in `compact_members`,
   written from the `runbook` contract at its normal depth. The manifest
   carries at most six (`query_catalog.COMPACT_DYNAMIC_CAP`); a runbook that
   stays a register row is named and evidenced, never written up as though
   its procedure had been verified.

Do not add sections beyond what the manifest's `compact_members` for this
document actually lists, and do not route readers into source files.

## Writing `docs/product-owner.md`

The compact product-owner file. It replaces
`docs/product/product-owner/README.md` and its children.

Write one `##` section per member the manifest actually selected, in
`compact_order`, grounding each section from the evidence its member contract
requires:

1. `## At a glance` — product-owner orientation: what this product delivers
   and how its value is measured.
2. `## Feature catalog` — `feature-catalog` (user outcome, audience,
   availability, owning flow). Describe outcomes, not the implementation
   inventory behind them.
3. `## Success metrics` — `success-metrics` (outcome, measure, instrumentation
   state, interpretation). State the instrumentation state honestly; a target
   the repository does not carry is an external token, never a number you
   supply.
4. `## Release notes` — `release-notes` (released user impact, version/date,
   compatibility impact, feature links). Keep internal refactors and
   dependency bumps out.
5. `## Backlog traceability` — `backlog-traceability`. **This section exists
   only when the repository carries ticket evidence.** Omit the heading
   entirely rather than emitting an empty seed table, and never map a ticket
   the evidence does not support.

Do not add sections beyond what the manifest's `compact_members` for this
document actually lists. Spilled siblings live in `docs/product/product-owner/`.

## Writing `docs/product.md`

The compact product file. Write one `##` section per member, in this reading
order, grounding each section from the evidence its member contract requires:

1. `## At a glance` — folder-index orientation (what the product area covers).
2. `## Overview` — `product-overview` (users, problems, capabilities, non-goals).

Do not add sections beyond the composed contract, and do not route readers into
source files.

## Writing `docs/reference.md`

The compact reference file. Write one `##` section per member the manifest
actually selected, in this reading order, grounding each section from the
evidence its member contract requires. The fifth section exists only when
the project is compact **and** Diligence or higher.

1. `## At a glance` — folder-index orientation (what a reader can look up here).
2. `## Configuration` — `configuration` (all configuration surfaces).
3. `## Limitations` — `limitations-register` (known limits with evidence).
4. `## Technology stack` — `tech-stack` (declared dependencies and tooling).
5. `## Glossary` — `glossary` (repository terms, precise definitions, and
   which document owns each). Link to the owning section instead of
   restating a term's definition there.

Do not add sections beyond what the manifest's `compact_members` for this
document actually lists, and do not route readers into source files.

## Writing `docs/security.md`

The compact security file. Exists only at Diligence or higher (security
content has no Spine members). Write one `##` section per member the
manifest selected, in this reading order, grounding each section from the
evidence its member contract requires:

1. `## At a glance` — folder-index orientation (security posture and scope).
2. `## Threat model` — `threat-model` (bounded DFD with zones, the
   element-by-STRIDE matrix, concrete threats each with exactly one
   disposition, testable controls/evidence, residual uncertainty, and
   accepted residual risk). Keep the analysis proportionate — the accepted-risk
   subsection is the reviewer's signal that analysis was performed. Never
   include disclosure workflow or credentials here.
3. `## Data handling` — `data-handling` (data classes, lifecycle, access,
   retention, deletion). Link `data-handling` classifications from the
   threat model above instead of restating them.

Do not add sections beyond what the manifest's `compact_members` for this
document actually lists, and do not route readers into source files.
