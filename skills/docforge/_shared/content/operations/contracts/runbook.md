# `runbook`

**Reader question** — "This alert is firing right now — what do I check first, and when do I stop and escalate?"

| Mode | Depth | Shape |
|---|---|---|
| How-to | deep-dive | diagnostic-path |

Written for an operator under pressure: safety and immediate mitigation come before the full diagnosis, and each diagnostic check selects the next action.

## Must present

| # | Element | At | Done wrong |
|---|---|---|---|
| 1 | The observable symptom, scope, and safety boundaries | L0 | an architecture tutorial substituted for incident action |
| 2 | Ordered diagnosis steps whose checks select the next action | L1 | a taxonomy of causes where a decision path was owed |
| 3 | Reversible mitigations where possible, destructive or high-impact actions behind explicit prerequisites | L2 | an unverified command presented as executable procedure |
| 4 | A verification signal after each remediation | L2 | a remediation with no checkable outcome |
| 5 | The escalation threshold, information to collect, and prevention follow-up | L3 | access or credentials assumed instead of stated as a prerequisite |

## Keep out

| Not here | Lives in |
|---|---|
| An architectural tutorial | `arch_low_level` |
| A deploy or recovery operation another document owns | `deployment`, `infra_disaster_recovery` |
| Signal definitions, correlation path, or alert intent | `observability` |
| Job-specific retry, backoff, or reliability guarantees | `worker_reliability` |

## Owns / links

| Owns | Links to | Because |
|---|---|---|
| Symptom, diagnosis, remediation, verification, escalation | `runbooks_index` | the register owns what each runbook recovers and its trigger |
| Deploy or recovery operations | `deployment`, `infra_disaster_recovery` | when those own the operation, link rather than restate |
