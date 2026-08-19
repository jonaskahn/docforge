# `diligence-index`

**Reader question** — "What has actually been verified across this portfolio, and where are the gaps?"

| Mode | Depth | Shape |
|---|---|---|
| Reference | reference | coverage-matrix |

Full coverage means one row per claim under review, grouped by diligence area, including every unsupported claim rather than omitting it.

## Must present

| # | Element | At | Done wrong |
|---|---|---|---|
| 1 | Rows grouped by diligence area (architecture, security, operations, dependencies) | lead | one flat list with no area grouping |
| 2 | Per claim: the claim, evidence found, a confidence level on a small fixed scale (confirmed / partial / unsupported), the remaining gap when confidence is less than high | the table | a prose hedge instead of a fixed confidence scale |
| 3 | Each evidence cell linked to a member document or repository-relative source path | the table | an area name with no concrete evidence link |
| 4 | A follow-up and evidenced owner token (or `undetermined`) for every partial or unsupported claim | the table | a claim promoted to a verdict without support |

## Keep out

| Not here | Lives in |
|---|---|
| A verdict — pass/fail, safe/unsafe | nowhere — this document maps evidence and gaps, judgment belongs to the reader |
| A repository discovery gap | `portfolio_repo_inventory` |

## Owns / links

| Owns | Links to | Because |
|---|---|---|
| Claim, evidence, confidence, gap, grouped by diligence area | every member repo's own architecture/security/operations documents | each claim's evidence traces to a specific member document; this document maps, never restates, that evidence |
| An unresolved gap in repository discovery | `portfolio_repo_inventory` | a claim about a repository that isn't fully inventoried traces its gap there |
