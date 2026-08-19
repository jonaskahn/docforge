# `disaster-recovery`

**Reader question** — "Deployment already failed — what do I do, in what order, and how do I know recovery actually worked?"

| Mode | Depth | Shape |
|---|---|---|
| How-to | deep-dive | diagnostic-path |

Stop conditions come before the full recovery procedure, per scenario: an operator needs to know when to escalate versus keep going before committing to the ordered steps.

## Must present

| # | Element | At | Done wrong |
|---|---|---|---|
| 1 | Per scenario: RTO and RPO as numbers, not aspirations | L0 | RTO/RPO stated as an aspiration instead of a measured number |
| 2 | Explicit stop conditions: what state means escalate vs. keep going | L0 | no stated boundary between "recovery is failing" and "keep going" |
| 3 | Recovery steps ordered by dependency, never by convenience | L1 | a downstream service brought up before its data store |
| 4 | A closing verification step that proves recovery succeeded, not just that commands ran | L2 | "wait for it to finish" instead of a checkable outcome |
| 5 | The data-loss boundary: the exact point in time data recovers to | L2 | "nothing was lost" implied instead of the exact boundary stated |

## Keep out

| Not here | Lives in |
|---|---|
| Ordinary deploy steps | `deployment` |
| Symptom-driven diagnosis | the relevant `runbook` |

## Owns / links

| Owns | Links to | Because |
|---|---|---|
| Scenarios, RTO/RPO, recovery order, data-loss boundary, escalation | `deployment` | ordinary deploy steps are owned there; this document starts where deployment failed |
| Symptom-driven diagnosis | the relevant `runbook` | diagnosis from the observable symptom is owned there |
