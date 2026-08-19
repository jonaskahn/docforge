# `process-flows`

**Reader question** — "In business terms, what happens when this process runs, and what if something goes wrong?"

| Mode | Depth | Shape |
|---|---|---|
| Explanation | deep-dive | entry-catalog |

One business-recognizable narrative per canonical flow, each entry preserving the business consequence of every branch.

## Must present

| # | Element | At | Done wrong |
|---|---|---|---|
| 1 | One entry per canonical flow: actor and trigger | per entry | internal component names exposed with no reader value |
| 2 | Ordered business actions, decision points, exceptions | per entry | a call chain pasted in place of a business narrative |
| 3 | Both successful and unsuccessful outcomes, preserving what is rejected, deferred, or escalated | per entry | an outcome's business consequence flattened into "handled" |

## Keep out

| Not here | Lives in |
|---|---|
| A raw call chain | the canonical `flow` document |
| A business rule's full definition, restated | `ba_business_rules` |

## Owns / links

| Owns | Links to | Because |
|---|---|---|
| The business narrative: actor, trigger, actions, decisions, outcomes | the canonical `flow` document | the technical sequence is owned there, linked not pasted |
| Formal logic of a referenced rule | `ba_business_rules` | the rule catalog owns definitions; this document names the rule only |
