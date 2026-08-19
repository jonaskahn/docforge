# `browser-support`

**Reader question** — "Which browsers does this actually run on, and what happens on the ones it doesn't?"

| Mode | Depth | Shape |
|---|---|---|
| Reference | reference | coverage-matrix |

_Aliased with: `ui-components`, `styling` (same content contract)._

The matrix table is the whole document: what full coverage means here is every browser this project claims to support, tested or manually verified, with its degradation behavior stated rather than left implicit.

## Must present

| # | Element | At | Done wrong |
|---|---|---|---|
| 1 | What "supported" means for this matrix: CI-tested or manually verified, stated once | lead | a browser marked supported with no stated evidence basis |
| 2 | Browser × minimum version × degradation behavior, one row per browser | the matrix | an invented support claim with no CI or manual-test evidence |
| 3 | Degradation stated per unsupported browser (polyfilled, reduced functionality, blocked outright) | the matrix | degradation left implicit |

## Keep out

| Not here | Lives in |
|---|---|
| A screenshot catalog | nowhere — the matrix is the evidence, not a gallery |
| Component-level degradation mechanism | `web_components` |
| OS/device-level compatibility | `platform_compatibility` |
| Styling approach and design tokens | `web_styling` |

## Owns / links

| Owns | Links to | Because |
|---|---|---|
| The tested browser × minimum-version matrix and per-browser degradation | `web_components` | component-level degradation behavior is owned there |
| — | `platform_compatibility` | the same tested-evidence discipline applies at OS/device level |
