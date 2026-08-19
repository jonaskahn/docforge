# `accessibility`

**Reader question** — "What accessibility conformance does this product actually target, and where does it fall short?"

| Mode | Depth | Shape |
|---|---|---|
| Reference | deep-dive | coverage-matrix |

_Aliased with: `localization` (same content contract)._

Full coverage means every WCAG success-criteria area has a row, including the ones not yet verified — never omitted because they weren't reviewed.

## Must present

| # | Element | At | Done wrong |
|---|---|---|---|
| 1 | The WCAG conformance level targeted (A/AA/AAA), per success-criteria area (perceivable, operable, understandable, robust) | the table | a compliance certification claimed with no evidence |
| 2 | The verification method per area (automated scan, manual audit, assistive-technology testing), named | the table | a verification result with no stated method |
| 3 | Known gaps, stated as plainly as covered areas, or an explicit "unaudited" | L3 | a nontrivial UI with no gaps section at all |

## Keep out

| Not here | Lives in |
|---|---|
| A compliance claim not evidenced | nowhere |
| Feature detail | `po_features` |
| Unresolved gaps left unlinked | `limitations` |

## Owns / links

| Owns | Links to | Because |
|---|---|---|
| The conformance claim: target level, per-area results, verification method | `po_features` | each supported interaction belongs to a feature owned there |
| Unverified areas and unresolved gaps | `limitations` | limits are listed and linked to their owner rather than buried here |
