# `triggers-and-jobs`

**Reader question** — "What triggers this job, can two instances run at once, and what happens downstream when it completes?"

| Mode | Depth | Shape |
|---|---|---|
| Explanation | deep-dive | entry-catalog |

## Must present

| # | Element | At | Done wrong |
|---|---|---|---|
| 1 | One entry per job or trigger: what triggers it (schedule, event, manual) | per entry | an owner named per system instead of per job |
| 2 | Payload shape | per entry | payload shape left unstated |
| 3 | Concurrency behavior: can it run overlapping instances, and what happens if it does | per entry | concurrency behavior left implicit |
| 4 | The downstream effect once it completes | per entry | an inferred downstream effect presented as evidenced |

## Keep out

| Not here | Lives in |
|---|---|
| Remediation detail for a misbehaving job | the relevant `runbook` |
| Flow steps started by a downstream effect | the relevant `flow` document |
| A data-shape guarantee in the payload | `dataset` or `data_flow` |

## Owns / links

| Owns | Links to | Because |
|---|---|---|
| Trigger, payload, scheduling, concurrency, ownership, downstream effects | operations `runbook`s | remediation for a misbehaving job is owned there; this document describes intended behavior only |
| A downstream effect that starts a flow | the relevant `flow` document | avoids re-deriving flow steps inside a job description |
| A data-shape guarantee in the payload | `dataset` or `data_flow` | schema/lineage detail is owned there, linked not restated |
