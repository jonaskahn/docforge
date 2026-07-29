# Flow writing craft

Name the flow as a reader-recognizable outcome, not a function name. Shape it like a BPMN
process read as prose: a start event, an end event, and gateways only where the process
actually branches.

Open with trigger, actors, and result — the start event, the lanes involved, the end event —
in one short paragraph. Number the happy path in plain language, one step per action, one
idea per sentence. Put branches immediately after the step that creates them, not gathered
at the end; a branch orphaned from its trigger step reads as a separate flow. Use a diagram
once the flow passes about four steps or has any branch: a flowchart for branching paths, a
sequence diagram when the interaction crosses actors or systems and order-in-time matters
more than choice. Keep lanes/actors to three or five; beyond that, split into linked
sub-flows rather than widening one diagram. End with failures and recovery, keeping shared
business rules linked rather than duplicated — a rule referenced by three flows lives once,
in the rule's own document.
