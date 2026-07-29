# Flow writing craft

**Preferred illustration:** Follow
[`../references/illustration.md`](../references/illustration.md); choose a
Mermaid flowchart for branches or a sequence diagram for cross-actor order.

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
budget. Split interactions that exceed that budget into linked sub-flows. End with failures and recovery, keeping shared
business rules linked rather than duplicated — a rule referenced by three flows lives once,
in the rule's own document.

## Composition and folders

When several small endpoint or service operations share one domain, compose them
into a single parent document with H2 sections instead of one stub each. Mark
members in the flow index as `doc_role: member` with `composed_into` set to the
parent id. Put related parents under `docs/flows/{family}/` when there are three
or more documentable siblings (for example `docs/flows/email/notification.md`
and `docs/flows/email/scheduled-reports.md`). Deferred candidates stay
index-only — do not leave symbol-named scaffold stubs in the tree.
