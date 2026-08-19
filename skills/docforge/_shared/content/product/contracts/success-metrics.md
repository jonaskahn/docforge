# `success-metrics`

**Reader question** — "How do we know this feature actually worked, and against what target?"

| Mode | Depth | Shape |
|---|---|---|
| Reference | deep-dive | lookup |

## Must present

| # | Element | At | Done wrong |
|---|---|---|---|
| 1 | One row per outcome: the desired change, separated from the measurable signal | the table | a recorded event presented as proof a target or outcome was achieved |
| 2 | Instrumentation source and coverage, interpretation, cadence, accountable owner | the table | a target, owner, or threshold inferred from telemetry alone |
| 3 | An external target token, or an explicit statement that no target is documented | the table | an invented target |
| 4 | Data quality or attribution limits that change how the measure can be read | the table | a data-quality limit left unstated |

## Keep out

| Not here | Lives in |
|---|---|
| An invented target, owner, or threshold | nowhere |
| Instrumentation implementation detail | `configuration` |

## Owns / links

| Owns | Links to | Because |
|---|---|---|
| Outcome, measurable signal, instrumentation state, interpretation | `po_features` | each outcome belongs to a feature owned there |
| Instrumentation and pipeline implementation | `configuration` | where the instrumentation is configured is owned there, linked not restated |
