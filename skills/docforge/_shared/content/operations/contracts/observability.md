# `observability`

**Reader question** — "How would I know if this system is unhealthy right now, and who gets paged?"

| Mode | Depth | Shape |
|---|---|---|
| Reference | deep-dive | answer-first |

Organized around the four golden signals — latency, traffic, errors, saturation — with alert intent stated as the governing claim before correlation detail.

## Must present

| # | Element | At | Done wrong |
|---|---|---|---|
| 1 | Per signal: what emits it, where it's visible (dashboard, log, trace) | L1 | a signal named with no stated source |
| 2 | Alert ownership and intent, stated distinctly ("page someone" vs. "log for later") | L2 | "page someone" and "log for later" conflated into one undifferentiated severity |
| 3 | Correlation: how a reader moves from an alert to the request/trace that caused it | L2 | correlation left unstated |
| 4 | Blind spots, named honestly: what this system cannot currently observe | L3 | only what can be observed listed, blind spots omitted |

## Keep out

| Not here | Lives in |
|---|---|
| Provider marketing | nowhere |
| What to do when a signal is bad | the linked `runbook` |
| Job-class failure and queue signals | `worker_reliability` |

## Owns / links

| Owns | Links to | Because |
|---|---|---|
| Signals, thresholds, routing, alert intent, blind spots | `runbook` | each actionable alert links to its runbook and escalation owner |
| — | `worker_reliability` | job-specific signals are owned there |
