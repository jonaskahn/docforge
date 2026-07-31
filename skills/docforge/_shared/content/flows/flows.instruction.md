# Flow (`flow`) writing craft

Default to an evidence-backed `sequenceDiagram`; use a flowchart only when branch
selection is the reader's primary question. Trace each step, branch, rule, and
failure to an entry point, handler, test, or trace, and link adjacent facts to
their owners rather than duplicating them.

Name the flow as a reader-recognizable outcome, not a function name. The file
slug and `display_name` in `.docforge/flow-index.json` must match that outcome
(for example `save-highlight`, never bare `save`). Shape it like a BPMN process
read as prose: a start event, an end event, and gateways only where the process
actually branches.

Open with trigger, actors, and result — the start event, the lanes involved, the end event —
in one short paragraph. Number the happy path in plain language, one step per action, one
idea per sentence. Put branches immediately after the step that creates them, not gathered
at the end; a branch orphaned from its trigger step reads as a separate flow. Add a visual
once the flow passes about four steps or has any branch, within the central complexity
budget. Split interactions that exceed that budget into linked sub-flows. End with failures and
recovery, keeping shared business rules linked rather than duplicated — a rule referenced by
three flows lives once, in the rule's own document.

## Illustration

- **Form:** Mermaid `flowchart` when the reader's question is "what are the branches and
  where do they go"; Mermaid `sequenceDiagram` when it is "in what order do the actors talk
  to each other" — pick one, never both for the same flow.
- **Renders:** for a flowchart, each gateway and its outcomes, labeled with the condition
  that selects them; for a sequence diagram, the actors as participants and each call as a
  labeled arrow, in the order they actually occur.
- **Trigger:** once the happy path passes about four steps, or as soon as any branch exists —
  per [`illustration.md`](../../references/illustration.md)'s deep-dive budget (at most 3
  illustrations, at most 12 elements per illustration).

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
