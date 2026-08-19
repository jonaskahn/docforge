# `limitations-register`

**Reader question** — "What is this system deliberately or currently unable to do, and is there a workaround?"

| Mode | Depth | Shape |
|---|---|---|
| Reference | deep-dive | entry-catalog |

## Must present

| # | Element | At | Done wrong |
|---|---|---|---|
| 1 | The register's four sections, each entry routed by a boundary test not a judgment call: Known limitations (deliberate trade-off), Known issues (defect under investigation), Not supported (no fix in flight), Scale and performance envelope (a tested numeric boundary) | lead | an entry placed by judgment instead of the boundary test |
| 2 | Per entry, in fixed order: trigger, impact, workaround, evidence | each entry | impact stated in implementation terms instead of the reader's terms |
| 3 | A review date on every entry | each entry | no review date, leaving "no such limitation" indistinguishable from "nobody looked" |
| 4 | Entries ordered by how often a reader hits them | the register | ordering by discovery date or file location |

## Keep out

| Not here | Lives in |
|---|---|
| Remediable engineering debt | `tech_debt` |
| A hard, externally imposed, immovable bound | `architecture_constraints` |
| A softened remediation hope presented as a promise | nowhere — "not currently planned" is honest, "coming soon" is a promise this document cannot keep |
| A hidden issue | nowhere — preserve it unowned rather than omitting it |

## Owns / links

| Owns | Links to | Because |
|---|---|---|
| Known limitations, known issues, not-supported, scale envelope | `tech_debt` | remediable engineering debt is routed there instead |
| Measured numeric boundaries | `performance_budgets` | budget rows share this register's dated-review discipline |
