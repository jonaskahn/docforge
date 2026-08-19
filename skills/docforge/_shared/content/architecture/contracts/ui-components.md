# `ui-components`

**Reader question** — "What does this component do, how does it compose, and which browsers does it degrade on?"

| Mode | Depth | Shape |
|---|---|---|
| Reference | reference | lookup |

_Aliased with: `styling`, `browser-support` (same content contract)._

## Must present

| # | Element | At | Done wrong |
|---|---|---|---|
| 1 | One row per component: responsibility, composition (slots, children, props contract) | the table | a screenshot gallery substituted for the composition contract |
| 2 | The token/theme it consumes rather than hardcodes | the table | a component API or token claim with no cited evidence |
| 3 | Evidence-backed support or degradation field | the table | the browser matrix reproduced instead of linked to `browser_support` |

## Keep out

| Not here | Lives in |
|---|---|
| A screenshot catalog | nowhere |
| The authoritative browser matrix | `browser_support` |
| Lifecycle mechanics | `app_lifecycle` |
| Render/state mechanics | `web_rendering`, `web_state` |

## Owns / links

| Owns | Links to | Because |
|---|---|---|
| Component responsibilities, composition, tokens/themes, browser matrix, degradation | `app_lifecycle` and `web_rendering`/`web_state` | lifecycle and render/state mechanics are owned there; this document owns only the component contract |
| A navigation-driving component | `app_ui_state` | navigation ownership is owned there, linked not restated |
