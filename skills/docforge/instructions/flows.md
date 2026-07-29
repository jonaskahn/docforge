# Flow writing craft

**Preferred illustration:** Follow
[`../references/illustration.md`](../references/illustration.md); choose a
Mermaid flowchart for branches or a sequence diagram for cross-actor order.

Name the flow as a reader-recognizable outcome, not a function name. Shape it like a BPMN
process read as prose: a start event, an end event, and gateways only where the process
actually branches.

Open with trigger, actors, and result — the start event, the lanes involved, the end event —
in one short paragraph. Number the happy path in plain language, one step per action, one
idea per sentence. Put branches immediately after the step that creates them, not gathered
at the end; a branch orphaned from its trigger step reads as a separate flow. Add a visual
once the flow passes about four steps or has any branch, within the central complexity
budget. Split interactions that exceed that budget into linked sub-flows. End with failures and recovery, keeping shared
business rules linked rather than duplicated — a rule referenced by three flows lives once,
in the rule's own document.
