# Adaptive flow deep dives

Load this reference after the flow's v3 analysis card is frozen. It turns the
card into a document whose shape follows the runtime evidence instead of a
catalog-wide heading shell.

## Start from the reader question

The opening must answer five universal questions: what starts the flow, what it
guarantees, how the evidenced runtime reaches a terminal outcome, what can stop
completion, and what remains unknown. Everything else is conditional. Use the
exact headings in `document_design.section_order`; do not borrow headings from
another flow merely because both have steps or failures.

For every ordered step, preserve the actor, source locator, boundary crossing,
synchronous or asynchronous handoff, input/output, and state change that the
analysis card evidences. Decisions, waits, loops, parallel branches, joins, and
rejoin points belong beside the step that creates them.

## Combine characteristics

A flow may carry several characteristics. Select every applicable row and merge
their concerns into the smallest coherent section design.

| Characteristic | Evidence-selected depth |
|---|---|
| `request-command` | Request contract and authorization context; authorization boundary; transaction commit/rollback boundary; response and error semantics; conditions under which retry is safe. |
| `event-message` | Envelope and correlation identity; delivery, ordering, and deduplication semantics; acknowledgement point; retry and dead-letter behavior; how the eventual outcome is verified. |
| `scheduled-batch` | Cadence and selection window; cursor/page/partition iteration; checkpoint durability; partial completion; restart and overlapping-run behavior. |
| `lifecycle-stateful` | State inventory; guarded and invalid transitions; concurrent transition behavior; rollback; terminal states. |
| `streaming-interactive` | Stream negotiation and setup; frame or chunk lifecycle; persistence point; graceful and abrupt cancellation; partial output; backpressure. |
| `fan-out-orchestration` | Branch trigger and ownership; all/any/N-of-M join or quorum; per-branch timeout; compensation; incomplete convergence. |
| `resource-lifecycle` | Allocation; readiness; ownership transfer; teardown order; interruption and leak behavior. |

The card's `modules` are independently selected evidence-backed concerns:
state, transaction, consistency, idempotency, ordering, deduplication, timing,
backpressure, security/authorization, observability, recovery, compensation,
and residual state. Omit a module only when it is not on
the card; never add a conventional section with no evidence.

## Choose diagrams by their question

`document_design.diagrams` is authoritative. A diagram is a view answering its
recorded `question`, not decoration.

- `sequenceDiagram` answers actor ordering: who calls or signals whom, which
  handoffs are asynchronous, and when a response returns.
- `flowchart` answers route selection: decision gateways, fan-out, merge or
  rejoin points, timeout routes, and dead-letter branches.
- `stateDiagram-v2` answers lifecycle movement: valid states, guarded
  transitions, invalid transitions, rollback, and terminal states.
- `text` answers a distinct terminal-outcome, residual-state, or timing question
  more clearly as a compact table, list, or structural fan-out.

Use the smallest set that answers the recorded questions. A flow does not get a
sequence diagram merely because the document catalog once named it the default.
If two diagrams answer the same question, keep the clearer one.

This follows the scenario-specific collaboration principle of
[C4 dynamic diagrams](https://c4model.com/diagrams/dynamic) and the separation
of activities, events, and gateways in
[OMG BPMN 2.0](https://www.omg.org/spec/BPMN/2.0.2/PDF/).

## Failures, recovery, and residue

Use only categories evidenced on the card:

1. `decision-rejected` — an authorization or business decision intentionally
   refuses progress.
2. `awaited-event-timeout` — an event the flow depends on does not arrive by
   its evidenced deadline.
3. `timeout` — an interaction or execution exceeds its evidenced time limit.
4. `interruption` — running work is stopped by shutdown, lease loss, process
   failure, or another external interruption.
5. `cancellation` — the initiator or controlling workflow intentionally
   cancels outstanding work.

For each failure, say what detects it, what happens immediately, which durable
or in-flight state remains, whether replay is safe, who performs recovery, and
where the flow rejoins or terminates. Compensation is a recovery strategy after
committed work, not a substitute for naming the triggering failure.

HTTP retry and idempotency claims must respect
[RFC 9110](https://www.rfc-editor.org/rfc/rfc9110.html). Event identity and
duplicate handling may use the
[CloudEvents specification](https://github.com/cloudevents/spec/blob/main/cloudevents/spec.md)
to explain protocol semantics, but only repository evidence can show that this
system implements those semantics.

## Causality and observability

Follow the causal path across process and service boundaries. Name propagated
context, correlation keys, spans, logs, metrics, and acknowledgement points only
when evidenced. [OpenTelemetry traces](https://opentelemetry.io/docs/concepts/signals/traces/)
may define trace terminology; they do not prove instrumentation exists in the
repository.

## Decomposition

Split a broad candidate into a parent overview and independent sub-flows only
when evidence shows separate guarantees, entry boundaries, failure domains, or
operational ownership. The analysis gate must show the hierarchy and rationale,
and `approved: true` must be present before `flow_index apply-analysis` creates
child rows.

The parent owns orientation, shared trigger context, child ordering, and the
overall guarantee. A child owns its entry boundary, steps, failures, residual
state, and terminal outcomes. Do not claim the same step in both. Close the
parent only after every selected child document exists.

## Research and provenance

External sources explain standards, frameworks, protocols, and vendor behavior;
they never establish what the repository implements. With research policy
`off`, retain the external question as an evidence gap. With approved research,
prefer standards, then official framework/protocol/vendor documentation, then
primary research.

Record approved material in provenance 2.2 `external_sources`, and attach its
source id through the relevant section's `external_refs`. Reader-facing links
belong only where external semantics materially change interpretation. Preserve
the source chain and access metadata using the concepts in
[W3C PROV-O](https://www.w3.org/TR/prov-o/).

## Evidence-gap honesty

Every unresolved `evidence_gaps` item remains explicit in the artifact, normally
as a concise "What remains unknown" note in the relevant section. Do not guess a
timeout, retry count, transaction boundary, deduplication key, recovery owner,
or rationale. A shorter document with a precise gap is complete; a filled-in
generic shell is not.
