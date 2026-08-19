# `assets-and-scenes`

**Reader question** — "What counts as a scene or asset here, and what happens when one is missing or corrupted?"

| Mode | Depth | Shape |
|---|---|---|
| Explanation | deep-dive | answer-first |

System boundaries come first, before the loading pipeline is traced in the order it actually happens.

_Aliased with: `gameplay-systems` (same content contract)._

## Must present

| # | Element | At | Done wrong |
|---|---|---|---|
| 1 | System boundaries: what counts as a scene or asset, where the loading pipeline's responsibility starts and ends | L0 | design-document aspiration instead of current behavior |
| 2 | Loading traced in actual order: discovery, load, instantiation, teardown | L1 | loading stages presented out of actual order |
| 3 | Save state: what is captured, what is regenerated instead of saved, and why | L1 | save-state behavior left unstated |
| 4 | Platform-build differences: asset formats, streaming behavior, memory budgets per target | L2 | a platform difference asserted without a build-configuration source |
| 5 | Failure behavior: missing asset, corrupted save, load timeout, and whether it fails safe, retries, or falls back | L2 | failure behavior omitted |

## Keep out

| Not here | Lives in |
|---|---|
| Design-document aspiration | nowhere — describe current behavior only |
| A platform-specific build difference's mechanism | `platform_integration` |
| A known loading shortcut | `tech_debt` |

## Owns / links

| Owns | Links to | Because |
|---|---|---|
| System boundaries, scenes/assets, loading, save state, platform builds | `arch_high_level` | this is the deep-dive of the asset/scene block named there |
| A platform-specific build difference | `platform_integration` | per-platform packaging/runtime detail is owned there; this document only notes that a difference exists |
| A known loading shortcut | `tech_debt` | a fixable shortcut in the pipeline is tracked there, not silently normalized here |
