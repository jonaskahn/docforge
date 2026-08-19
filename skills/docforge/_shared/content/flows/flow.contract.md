# `flow`

**Reader question** — "What happens, in order, when this trigger fires, and what am I guaranteed?"

| Mode | Depth | Shape |
|---|---|---|
| Explanation | deep-dive | ordered-narrative |

Sequence is the spine: a reader arrives mid-question and travels forward through what the system does, from trigger to outcome.

## Must present

| # | Element | At | Done wrong |
|---|---|---|---|
| 1 | The guarantee, stated before any mechanism | L0 | mechanism explained before the guarantee is stated |
| 2 | Trigger and actors, split by what the initiator can see | L1 | actors listed flat, initiator visibility not distinguished |
| 3 | Ordered happy-path steps, each one hop with a `file:line` grounding | L1 | a subsystem paraphrase standing in for a step |
| 4 | Branches, each beside the step that creates it, with its condition and rejoin point | L2 | branches gathered in a section away from their triggering step |
| 5 | Failures, each assigned one of the evidenced categories (rejected decision, awaited event, timeout, interruption, cancellation) | L2 | a technical retry the caller never observes written up as a failure mode |
| 6 | Data in play, timing/limits, and the observability signal, each only where evidenced | L2 | an estimated timeout or invented signal in place of an honest omission |
| 7 | The outcome, restated in full, and the force that shaped this flow's shape when a decision record exists | L3 | speculative rationale with no decision record and no visible constraint |

## Keep out

| Not here | Lives in |
|---|---|
| Hand-inferred flow inventory or discovery status | `flow-index` |
| A business rule referenced by three or more flows | the rule's own document |
| A step that crosses a system boundary named in `architecture-high-level` | the relevant architecture block |
| Implementation mechanism beyond a one-line gist, once promoted | the flow's `engineering.md` subfile |
| BA rules and requirement traceability, once promoted | the flow's `business-analyst.md` subfile |
| The business-recognizable narrative of the same work | `ba_process_flows` |
| Feature value, status, or audience framing | `po_features` |

## Owns / links

| Owns | Links to | Because |
|---|---|---|
| Trigger, actors, ordered steps, branches, failures, outcome | its `flow-index` row in `docs/flows/README.md` | the index tracks discovery status, priority, and confidence, never the steps themselves |
| — (once promoted) | its own `business-analyst.md` and `engineering.md` subfiles | each subfile links back to this flow rather than restating its steps |
