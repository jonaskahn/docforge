# `styling`

**Reader question** — "What design tokens exist, and how does theming actually work?"

| Mode | Depth | Shape |
|---|---|---|
| Reference | reference | lookup |

_Aliased with: `ui-components`, `browser-support` (same content contract)._

## Must present

| # | Element | At | Done wrong |
|---|---|---|---|
| 1 | The token system as data: name and value, not prose description | the table | tokens described in prose instead of listed as data |
| 2 | How theming actually works (CSS variables, a theme provider, build-time generation) | L2 | the theming mechanism left unstated |
| 3 | Degradation behavior when a token is missing | L2 | a missing-token fallback left implicit |

## Keep out

| Not here | Lives in |
|---|---|
| Component composition and general hierarchy | `web_components` |
| Support policy, accessibility, or performance claims | `browser_support`, `accessibility`, `performance_budgets` |
| A screenshot catalog | nowhere |

## Owns / links

| Owns | Links to | Because |
|---|---|---|
| The token/theme system, degradation when a token is missing | `web_components` | component composition and general hierarchy are owned there |
| Support policy, accessibility, performance claims | `browser_support`, `accessibility`, `performance_budgets` | each claim is linked to its owner, not restated |
