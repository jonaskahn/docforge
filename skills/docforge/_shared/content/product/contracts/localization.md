# `localization`

**Reader question** — "Which locales does this product actually support, and what happens when a translation is missing?"

| Mode | Depth | Shape |
|---|---|---|
| Reference | deep-dive | lookup |

_Aliased with: `accessibility` (same content contract)._

## Must present

| # | Element | At | Done wrong |
|---|---|---|---|
| 1 | One row per supported locale: coverage (fully translated, partial, machine-translated — name which) | the table | a locale marked "supported" when only partially translated |
| 2 | Fallback behavior when a string or locale isn't available | the table | fallback behavior left unstated |
| 3 | The resource format: file type and where translated strings actually live | the table | file presence alone presented as proof of support |

## Keep out

| Not here | Lives in |
|---|---|
| A compliance claim not evidenced | nowhere |
| Partial coverage or unsupported locales left unlinked | `limitations` |

## Owns / links

| Owns | Links to | Because |
|---|---|---|
| The supported-locale table, coverage, fallback behavior | `limitations` | partial coverage and unsupported locales are user-visible limits, stated with the same evidence discipline |
