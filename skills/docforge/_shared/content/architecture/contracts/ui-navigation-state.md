# `ui-navigation-state`

**Reader question** — "Which store owns this navigation surface's state, and what survives a transition?"

| Mode | Depth | Shape |
|---|---|---|
| Explanation | deep-dive | entry-catalog |

## Must present

| # | Element | At | Done wrong |
|---|---|---|---|
| 1 | One entry per navigation surface: who owns its state (global store, local component state, platform navigation stack) | per surface | visual design tokens presented as a navigation concern |
| 2 | How state survives or resets across a transition | per surface | restoration behavior asserted with no navigation or code-graph evidence |
| 3 | Restoration behavior on process death, and error presentation per surface | per surface | tested restoration/error behavior left unmarked when actually unknown |

## Keep out

| Not here | Lives in |
|---|---|
| Visual design tokens | `web_styling` |
| Process-lifecycle restoration mechanics | `app_lifecycle` |

## Owns / links

| Owns | Links to | Because |
|---|---|---|
| Surfaces, navigation, state ownership, transitions, restoration, error presentation | `web_components` | visual design tokens are owned there; this document owns only navigation state |
| Restoration behavior after an app-lifecycle transition | `app_lifecycle` | process-death restoration is a lifecycle concern owned there, linked not restated |
