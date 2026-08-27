# Flows writing craft

Writing-craft instructions for `flows` group documents. Routes:

- `flows_index` → [Flow index (`flow-index`)](#flow-index-flow-index-writing-craft)
- `flow` → [Flow (`flow`)](#flow-flow-writing-craft)

## Voice and linking craft

Voice for this group is owned by [`voice.md`](../../references/voice.md):
narrative and ordered, one idea per sentence, the branch right under the step
that creates it. When linking to a fact another document owns — the
flow-index row, a promoted subfile, a shared business rule, an architecture
boundary — name what that document owns before the link, never "see
`foo.md`." What each side of a link owns, and why it is linked rather than
restated, is each contract's `## Owns / links` table, not this section.

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

This document is the human-readable projection of
`.docforge/flow-index.json`, never a second source of truth for it.

## Flow (`flow`) writing craft

Start from the selected flow's `reader_question` and frozen
`document_design`; there is no default diagram or heading sequence. Trace each
step, branch, rule, and failure to an entry point, handler, test, or trace, and
link adjacent facts to their owners rather than duplicating them.

Name the flow as a reader-recognizable outcome, not a function name. The file
slug and `display_name` in `.docforge/flow-index.json` must match that outcome
(for example `save-highlight`, never bare `save`). Shape it like a BPMN process
read as prose: a start event, an end event, and gateways only where the process
actually branches.

Work from the deep pack at `.docforge/flow-analysis.json` (and the row's
`evidence` in `.docforge/flow-index.json`), which already carries the ordered
steps with their locators, the branches, the rules, and the failures. Do not
re-derive the step order by grep — that is what the pack exists to prevent.
The row must have `analysis_state: ready`, and the analysis card must have a
selected decision, before writing starts. Load
[`flow-deep-dive.md`](../../references/flows/flow-deep-dive.md) for
characteristic modules, decomposition boundaries, research provenance, and
diagram selection.

**A step is one hop with a `file:line` grounding**, not a paraphrase of a
subsystem. "Content is indexed into Elasticsearch" naming only a file is a
summary; a named symbol with a `path/to/file.js:88` locator is a step. That
locator is the grounding standard — it belongs in provenance, never in the
step's prose, which names the actor and the action (see
[`evidence-presentation.md`](../../references/evidence-presentation.md)).
Where the pack marks a step `evidence: "source"` rather than `"graph"`, cite
the file you read it in.

Open with what initiates the flow, who depends on it, and its guarantee before
any mechanism. Then expand the headings in `document_design.section_order` in
that exact order. Section names are evidence-specific: a request flow may need
"Authorization and commit boundary", an event consumer may need "Delivery,
acknowledgement, and replay", and a lifecycle flow may need "Guarded state
transitions". Do not normalize those back into a shared seven-heading shell.

Keep branches, waits, loops, parallel splits, joins, and recovery next to the
step that creates them unless the analysis card deliberately assigns a distinct
section to answer a different reader question. Use every selected module and
diagram question, surface every evidence gap, and delete template-shaped filler.

## Adaptive depth and diagrams

L0 is always the opening and guarantee. L1 carries the core causal path and
terminal outcomes. L2 carries the evidenced decisions, waits, concurrency,
failure, recovery, and characteristic-specific modules needed to operate or
change the flow. L3 is reserved for evidenced constraints or decision records.
The card decides which headings carry those altitudes.

Render only the forms named in `document_design.diagrams`: sequence for actor
ordering, flowchart for gateways/fan-out/rejoin, state diagram for lifecycle
transitions, and structural text for a distinct terminal-outcome or timing
question. Each diagram must answer its recorded question; no flow receives a
sequence diagram by convention.

## Composition and folders

Do not split or compose on naming similarity alone. Apply a decomposition only
when its analysis proposal is approved and it identifies separate guarantees,
entry boundaries, failure domains, or operational owners. Approved independent
children are standalone rows with `parent_flow`; payload-only composed members
remain `doc_role: member` with `composed_into`. A parent overview closes only
after its child artifacts exist. Put a hierarchy under the approved
`family_path`, and keep deferred candidates index-only without scaffold stubs.
