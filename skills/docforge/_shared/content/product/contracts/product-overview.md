# `product-overview`

**Reader question** — "What does this product do for me, and is it worth a deeper look?"

| Mode | Depth | Shape |
|---|---|---|
| Explanation | orientation | answer-first |

Shaped like a compressed PR/FAQ: the job the reader hires the product to do comes before any capability list.

## Must present

| # | Element | At | Done wrong |
|---|---|---|---|
| 1 | Who the product is for and the problem it changes, as a job-to-be-done ("when X happens, this lets you Y") | L0 | a persona bio instead of a job-to-be-done statement |
| 2 | Main capabilities as outcomes the reader gets, not modules the team built | L1 | implementation vocabulary not part of the product's user contract |
| 3 | Boundaries and explicit non-goals, stated as plainly as the capabilities | L2 | non-goals omitted or softened |
| 4 | Links out: flows for behavior depth, capability and reference material for detail | L3 | a claim needing a table or diagram left unlinked instead of routed to its owner |

## Keep out

| Not here | Lives in |
|---|---|
| Invented roadmap or implementation detail | nowhere |
| Capability detail per feature | `po_features` |
| Behavior depth | the relevant `flow` documents |

## Owns / links

| Owns | Links to | Because |
|---|---|---|
| Users, problems, capabilities, non-goals | `po_features` | capability detail is owned per feature there |
| Behavior depth | the relevant `flow` documents | owned there, routed not restated |
