# `gameplay-systems`

**Reader question** — "What does this gameplay system own, and what survives across a session?"

| Mode | Depth | Shape |
|---|---|---|
| Explanation | deep-dive | entry-catalog |

_Aliased with: `assets-and-scenes` (same content contract)._

## Must present

| # | Element | At | Done wrong |
|---|---|---|---|
| 1 | One entry per system: its boundary (what it owns, what it doesn't) | per system | design-document aspiration instead of what's implemented |
| 2 | Its save-state contract: what persists across sessions and how | per system | save-state semantics left unstated |
| 3 | Recovery for missing/corrupt assets and incompatible saved state, when evidenced, otherwise marked unknown | per system | recovery behavior invented instead of marked unknown |

## Keep out

| Not here | Lives in |
|---|---|
| Design-document aspiration | nowhere — describe what's implemented |
| The scene graph, load/unload dependencies, asset pipeline | `game_assets` |
| A platform-specific asset pipeline difference | `platform_integration` |
| A known loading or save-state shortcut | `tech_debt` |

## Owns / links

| Owns | Links to | Because |
|---|---|---|
| System boundaries, event/update ordering, save-state semantics | `arch_high_level` | this is the deep-dive of the gameplay block named there |
| Scene graph, load/unload dependencies, asset pipeline, target variance | `game_assets` | owns its own instruction; keeps runtime systems distinct from asset loading |
| A platform-specific asset pipeline difference | `platform_integration` | per-platform packaging/runtime detail is owned there |
| A known loading or save-state shortcut | `tech_debt` | a fixable shortcut is tracked there, not normalized into the description here |
