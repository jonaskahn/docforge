# `feature-catalog`

**Reader question** — "What can a user actually do with this product, and is it really shipped?"

| Mode | Depth | Shape |
|---|---|---|
| Reference | deep-dive | entry-catalog |

## Must present

| # | Element | At | Done wrong |
|---|---|---|---|
| 1 | One row per externally reachable capability: outcome, audience | the table | product intent inferred from a module name alone |
| 2 | Availability/delivery state (implemented, enabled, preview, planned), distinguished only when evidence supports it | the table | "shipped" claimed with no release or deployment evidence |
| 3 | Material constraints and the owning flow link | the table | behavior duplicated here instead of linked to the flow |
| 4 | Rows ordered by reader value or journey | the table | a module inventory ordered by codebase structure |

## Keep out

| Not here | Lives in |
|---|---|
| An implementation inventory | that feature's owning `flow` document |
| Shared positioning | `product_overview` |

## Owns / links

| Owns | Links to | Because |
|---|---|---|
| Each feature's outcome, audience, availability, constraints | its owning `flow` document | behavior is owned there, linked not duplicated |
| Shared positioning and boundary statements | `product_overview` | the product frame is owned there |
