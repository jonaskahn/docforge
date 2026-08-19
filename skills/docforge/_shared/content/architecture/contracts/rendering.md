# `rendering`

**Reader question** — "Where does rendering actually happen, and what does the boundary do when it fails?"

| Mode | Depth | Shape |
|---|---|---|
| Explanation | deep-dive | answer-first |

Where rendering occurs (server, client, handoff) is the governing claim, before individual transitions.

_Aliased with: `state-management` (same content contract)._

## Must present

| # | Element | At | Done wrong |
|---|---|---|---|
| 1 | Where rendering occurs, and the server/client handoff when present | L0 | hydration, persistence, or route behavior inferred from framework defaults |
| 2 | The render lifecycle (mount, update, unmount) and what triggers each transition | L1 | a transition with no cited trigger or evidence |
| 3 | Loading and error presentation | L2 | the component catalog restated instead of linked |
| 4 | Render-boundary recovery | L2 | recovery behavior omitted |

## Keep out

| Not here | Lives in |
|---|---|
| The component catalog | `web_components` |
| Persisted state surviving a render cycle | `persistence` |
| Navigation-triggered state changes | `app_ui_state` |

## Owns / links

| Owns | Links to | Because |
|---|---|---|
| Lifecycle, boundaries, transitions, failure and recovery behavior | `web_components` | the component catalog is owned there; this document owns only the render/state mechanism |
| Persisted state surviving a render cycle | `persistence` | durability mechanics are owned there |
| Navigation-triggered state changes | `app_ui_state` | avoids re-deriving navigation state here |
