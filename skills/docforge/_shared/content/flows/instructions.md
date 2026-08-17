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

Open with trigger, actors, and result in one short paragraph. Number the happy path in
plain language, one step per action, one idea per sentence. Put branches immediately
after the step that creates them, not gathered at the end; a branch orphaned from its
trigger step reads as a separate flow. Add a visual once the flow passes about four steps
or has any branch, within the central complexity budget. Split interactions that exceed
that budget into linked sub-flows. End with failures and recovery, keeping shared
business rules linked rather than duplicated.

## Illustration

- **Form:** Mermaid `flowchart` when the reader's question is "what are the branches and
  where do they go"; Mermaid `sequenceDiagram` when it is "in what order do the actors talk
  to each other"; Mermaid `journey` when it is "how did the experience feel across the
  process for a given actor" (effort or satisfaction per step) — pick exactly one form,
  never more than one, for the same flow.
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

## Composition and folders

When several small endpoint or service operations share one domain, compose them
into a single parent document with H2 sections instead of one stub each. Mark
members in the flow index as `doc_role: member` with `composed_into` set to the
parent id. Put related parents under `docs/flows/{family}/` when there are three
or more documentable siblings (for example `docs/flows/email/notification.md`
and `docs/flows/email/scheduled-reports.md`). Deferred candidates stay
index-only — do not leave symbol-named scaffold stubs in the tree.
