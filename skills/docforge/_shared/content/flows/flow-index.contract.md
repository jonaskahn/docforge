# `flow-index`

**Reader question** — "What flows has this repository been analyzed for, and which one do I open?"

| Mode | Depth | Shape |
|---|---|---|
| Reference | orientation | coverage-matrix |

The row set is the claim: every evidence-backed candidate appears, whether or not it earned a written flow, so the matrix states discovery coverage, not just a table of contents.

## Must present

| # | Element | At | Done wrong |
|---|---|---|---|
| 1 | The status vocabulary, stated once: `main` / `deferred` / `placeholder` / `documented` / `skipped` | L0 | a status used without ever being defined |
| 2 | Rows grouped by family (or "Ungrouped"), sorted by evidenced priority within each group, main before deferred | L1 | sorting by assumed reach instead of evidenced priority |
| 3 | Per row: normalized entry reference, area, confidence, reach, priority, status | L1 | a row for a heuristic guess or an invented execution order |
| 4 | A `member` row's `composed_into` parent id | L2 | duplicating the member's content here instead of pointing at the parent section |
| 5 | Every candidate the discovery pass found, including deferred, placeholder, and skipped rows | L2 | dropping a low-confidence candidate instead of recording it as deferred or skipped |

## Keep out

| Not here | Lives in |
|---|---|
| The flow's steps, branches, or failures | the `flow` document, once it exists |
| Business rule logic | `ba_business_rules` |
| A relationship diagram of the flow set | nowhere — this document is Markdown table only |

## Owns / links

| Owns | Links to | Because |
|---|---|---|
| Discovery status, role, area, confidence, reach for every candidate | each `standalone`/`main` row's `flow` document | the index routes; the flow document owns the actual steps |
| A `member` row's `composed_into` id | the parent flow document's matching H2 section | keeps composed members traceable without duplicating their content here |
