# `performance-budgets`

**Reader question** — "How close is this system to its measured resource limits, and what happens if it's exceeded?"

| Mode | Depth | Shape |
|---|---|---|
| Reference | reference | lookup |

## Must present

| # | Element | At | Done wrong |
|---|---|---|---|
| 1 | One row per budget: evidenced limit (CPU/GPU/memory/storage/timing), measurement method (load test, profiler, production observation — name which), what degrades when approached or exceeded | the table | a target stated with no actual measurement behind it |
| 2 | Measurement recency, dated the way `limitations-register` dates its review | the table | an undated measurement |
| 3 | Rows ordered by how often a reader hits the budget in practice | the table | alphabetical ordering by resource type |

## Keep out

| Not here | Lives in |
|---|---|
| An invented target | nowhere — never state a target that hasn't been measured |
| Detailed user-visible remediation | `limitations` |

## Owns / links

| Owns | Links to | Because |
|---|---|---|
| Each budget's evidenced limit, measurement, degradation | `limitations` | user-visible limits date their review the way this document dates its measurements |
