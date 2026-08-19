# `job-reliability`

**Reader question** — "For this job class, what's the retry policy, and is it actually safe to retry?"

| Mode | Depth | Shape |
|---|---|---|
| Reference | deep-dive | lookup |

## Must present

| # | Element | At | Done wrong |
|---|---|---|---|
| 1 | One row per job class, each reliability property as a concrete fact: retry count and backoff shape, the exact idempotency key or mechanism, the timeout value and its behavior | the table | "retries" or "idempotent" stated as a category label instead of the concrete mechanism |
| 2 | Backpressure behavior | the table | a job that retries with no stated idempotency mechanism, and no note that this is a duplicate-side-effect risk |
| 3 | The dead-letter and replay path together: where failed jobs land, and the actual replay procedure | the table | dead-letter location stated with no replay procedure |
| 4 | An authorized replay role and integrity check | the table | replay described with no authorization check |

## Keep out

| Not here | Lives in |
|---|---|
| Business process duplication | the owning `flow` document |
| Job identity, triggers, and payload detail | `worker_triggers` |
| Signal visibility and alert ownership | `observability` |

## Owns / links

| Owns | Links to | Because |
|---|---|---|
| Failure handling per job class: retry, idempotency, replay | `worker_triggers` | job identity, triggers, and payloads are owned there |
| Failure, lag, and queue signals' visibility and alert ownership | `observability` | signal → source → alert intent is owned there, linked not copied |
