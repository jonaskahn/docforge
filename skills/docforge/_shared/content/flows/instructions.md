# Flows writing craft

Writing-craft instructions for `flows` group documents. Routes:

- `flows_index` → [Flow index (`flow-index`)](#flow-index-flow-index-writing-craft)
- `flow` → [Flow (`flow`)](#flow-flow-writing-craft)

## Flow index (`flow-index`) writing craft

Every candidate row includes an evidence locator, confidence basis, and explicit
priority; sort by that evidenced priority, never by assumed reach. Retain
unresolved candidates as `placeholder` or `skipped`, not inferred flows.

This is the router for the whole flow layer, not a flow itself: a reader
scans it to decide which flow to open, or whether a candidate they expected
even surfaced. Group rows by family (or "Ungrouped") and sort by priority
within a group, main before deferred. State the status vocabulary once at the
top: `main` / `deferred` / `placeholder` / `documented` / `skipped`.

Every row must trace to an evidenced candidate; never add a row for a
heuristic guess or an invented execution order. `standalone` rows get their
own deep-dive document; `member` rows are folded into a parent under
`composed_into`; `index_only` rows stay discoverable without a stub file.
Keep the row itself terse — trigger kind, normalized entry signature, area,
confidence, reach — and never restate the flow's steps, branches, or failures
here; those belong solely to the `flow` document once it exists.

## Illustration

- **Form:** Markdown table only.
- **Renders:** nothing beyond the table; do not add a relationship diagram
  even for a large flow set.
- **Trigger:** never — orientation depth caps this document at prose plus
  the table itself, per [`illustration.md`](../../references/illustration.md).

## Connections

| This document owns | Links to | Because |
|---|---|---|
| Discovery status, role, area, confidence, reach for every candidate | each `standalone`/`main` row's `flow` document | the index routes; the flow document owns the actual steps |
| — | `.docforge/flow-index.json` (declared as the machine-readable source of truth) | this document is the human-readable projection of that file, never a second source of truth |
| A `member` row's `composed_into` id | the parent flow document's matching H2 section | keeps composed members traceable without duplicating their content here |

## Voice

- **Voice:** narrative and ordered; one idea per sentence; branch beside its step.

## Flow (`flow`) writing craft

Default to an evidence-backed `sequenceDiagram`; use a flowchart only when branch
selection is the reader's primary question. Trace each step, branch, rule, and
failure to an entry point, handler, test, or trace, and link adjacent facts to
their owners rather than duplicating them.

Name the flow as a reader-recognizable outcome, not a function name. The file
slug and `display_name` in `.docforge/flow-index.json` must match that outcome
(for example `save-highlight`, never bare `save`). Shape it like a BPMN process
read as prose: a start event, an end event, and gateways only where the process
actually branches.

Work from the deep pack at `.docforge/flow-analysis.json` (and the row's
`evidence` in `.docforge/flow-index.json`), which already carries the ordered
steps with their locators, the branches, the rules, and the failures. Do not
re-derive the step order by grep — that is what the pack exists to prevent.

**A step is one hop with a `file:line` grounding**, not a paraphrase of a
subsystem. "Content is indexed into Elasticsearch" naming only a file is a
summary; a named symbol with a `path/to/file.js:88` locator is a step. That
locator is the grounding standard — it belongs in provenance, never in the
step's prose, which names the actor and the action (see
[`evidence-presentation.md`](../../references/evidence-presentation.md)).
Where the pack marks a step `evidence: "source"` rather than `"graph"`, cite
the file you read it in.

Open with what the flow produces and who depends on it, then state the guarantee
before any mechanism. Number the happy path in plain language, one step per action,
one idea per sentence. Put branches immediately after the step that creates them,
not gathered at the end; a branch orphaned from its trigger step reads as a separate
flow. Add a visual once the flow passes about four steps or has any branch, within
the central complexity budget. Split interactions that exceed that budget into linked
sub-flows. End with failures and recovery, keeping shared business rules linked
rather than duplicated.

A worked example of everything below is
[`flow.standard.example.md`](../shared/exemplars/flow.standard.example.md), with
its folded counterpart at
[`flow.compact.example.md`](../shared/exemplars/flow.compact.example.md). Read
them when a field's intent is unclear; they are craft references, not templates.

## Level discipline

This document is ordered per
[`progressive-disclosure.md`](../../references/progressive-disclosure.md).

| Level | Sections |
|---|---|
| L0 — answer | the opening paragraph and `**Guarantee:**` |
| L1 — shape | `## Trigger and actors`, `## Happy path` and its diagram |
| L2 — detail | `## Branches and rules`, `## Failure and recovery`, `## Observability` |
| L3 — boundary | `## Outcome`, `## Why it works this way`, the `Related` footer |

The guarantee appears twice on purpose — once at L0 so a reader who stops at
the top is still correct, once in full under `## Outcome`. That is the only
licensed repetition in the document.

The happy path names steps; it never explains one. A step that needs a
paragraph of conditions has a branch, and the branch belongs in
`## Branches and rules` with its own sub-heading. The primary diagram is an L1
obligation for the same reason: it carries the happy path, never annotated
branch outcomes.

Group the happy path under milestone sub-headings only once it passes about six
steps — a milestone is a point at which the work is durably further along, not
an arbitrary split. Below six steps, number the steps flat.

## Failure categories

Failure modes come in kinds, and a flow document that names only the kind it
happened to trip over has not analyzed the flow. Walk the evidence for each of
these and write up the ones it supports:

- a decision this flow makes and rejects;
- an external event it waits for that does not arrive as expected;
- a response that never comes within its timeout;
- an interruption while a step is running;
- a cancellation that can arrive at almost any point.

Delete the categories the evidence does not support; never invent one to
complete the set. A technical retry the caller never observes is mechanism, not
a failure mode — it belongs under **Immediate response**, never as its own
entry. The distinction is what keeps this section about what a reader must
handle rather than about what the framework does on its own.

## Evidence-gated sections

`**Data in play:**`, `**Timing and limits:**`, `## Observability`, and
`## Why it works this way` are deleted when the repository does not evidence
them. Deleting is the correct outcome, not a gap — an estimated timeout or a
reconstructed rationale is worse than a shorter document. In particular:

- `## Observability` names the signal and its healthy value; the runbook owns
  what to do when the signal is bad.
- `## Why it works this way` links the decision record when one exists and adds
  at most one sentence naming the force it settled. Prose without a decision
  record is allowed only for a constraint visible in the repository — a pin, a
  documented limit, a code comment, a migration commit.

## Illustration

- **Form:** one **primary** form answering the flow's main question — Mermaid
  `sequenceDiagram` for "in what order do the actors talk to each other",
  `flowchart` for "what are the branches and where do they go", `journey` for
  "how did the experience feel across the process for a given actor". Pick one
  primary form; a second diagram is permitted only when it answers a
  *different* question, and only in its own section: the ASCII
  trigger-to-outcome fan-out under `## Outcome` when the flow has two or more
  terminal outcomes. Never two diagrams of the same shape restating each other.
- **Renders:** for a flowchart, each gateway and its outcomes, labeled with the condition
  that selects them; for a sequence diagram, the actors as participants and each call as a
  labeled arrow, in the order they actually occur; for a journey, the steps grouped into
  sections by phase, each step scored 1-5 with the actor who experiences it.
- **Trigger:** once the happy path passes about four steps, or as soon as any branch exists —
  per [`illustration.md`](../../references/illustration.md)'s deep-dive budget.

## Connections

| This document owns | Links to | Because |
|---|---|---|
| Trigger, actors, ordered steps, branches, failures, outcome | its `flow-index` row in `docs/flows/README.md` | the index tracks discovery status/priority/confidence, never the steps themselves — one owner per fact |
| — (once promoted) | its own `business-analyst.md` subfile | BA rules and requirement traceability link back to this flow; they never restate its steps |
| — (once promoted) | its own `engineering.md` subfile | implementation mechanism links back; this document keeps only a one-line gist |
| A business rule referenced by 3+ flows | the rule's own document | never duplicated per-flow; link, don't restate |
| A step that crosses a system boundary named in `architecture-high-level` | the relevant architecture block | avoids re-deriving the box diagram inside flow prose |

## Voice

- **Voice:** narrative and ordered; one idea per sentence; branch beside its step.

## Composition and folders

When several small endpoint or service operations share one domain, compose them
into a single parent document with H2 sections instead of one stub each. Mark
members in the flow index as `doc_role: member` with `composed_into` set to the
parent id. Put related parents under `docs/flows/{family}/` when there are three
or more documentable siblings (for example `docs/flows/email/notification.md`
and `docs/flows/email/scheduled-reports.md`). Deferred candidates stay
index-only — do not leave symbol-named scaffold stubs in the tree.
