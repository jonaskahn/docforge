# `portfolio-operations`

**Reader question** — "What operational dependency is shared across repos, and what happens portfolio-wide when it degrades?"

| Mode | Depth | Shape |
|---|---|---|
| Explanation | deep-dive | lookup |

Written at the seam between repositories, not inside any one of them.

## Must present

| # | Element | At | Done wrong |
|---|---|---|---|
| 1 | Each shared operational dependency (a queue, a shared datastore, a shared on-call rotation), named | lead | member-level detail restated instead of the cross-repo seam |
| 2 | What happens across the portfolio when the dependency degrades, with blast radius | the table | local severity stated with no portfolio-wide blast radius |
| 3 | Status, evidence and as-of date, accountable follow-up per row | the table | a row with no evidence or as-of date |

## Keep out

| Not here | Lives in |
|---|---|
| A finding that is really about one repository's internals | that repo's own `observability` |
| Member-level detail that adds no cross-repo information | nowhere — omit it |

## Owns / links

| Owns | Links to | Because |
|---|---|---|
| Cross-repo shared dependencies and operational coupling | each member repo's own `observability` document | member-internal findings are owned there; this document owns only the cross-repo seam |
| A shared dependency also named in a member's `dependencies` | that member's `dependencies` | this document adds the cross-repo blast radius; the member document owns its own criticality judgment |
| An unresolved cross-repo gap | `portfolio_diligence_index` | tracks the confidence gap until a member closes it |
