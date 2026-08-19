# `platform-compatibility`

**Reader question** — "Which OS, device, and architecture combinations does this actually run on, tested?"

| Mode | Depth | Shape |
|---|---|---|
| Reference | reference | coverage-matrix |

The matrix table is the whole document: full coverage means every OS/device/architecture combination this project claims support for, each with tested minimums and degradation stated.

## Must present

| # | Element | At | Done wrong |
|---|---|---|---|
| 1 | OS/device/architecture matrix with tested minimums | the matrix | a minimum stated as aspiration rather than tested evidence |
| 2 | Degradation behavior below the minimum (refuses to run, runs with reduced features) | the matrix | unverified target support inferred from a build artifact |
| 3 | The deprecation horizon for older supported platforms | the matrix | a deprecation horizon left unstated |

## Keep out

| Not here | Lives in |
|---|---|
| Release procedure | `release_guide` |
| Permission and lifecycle behavior | `platform_permissions` |

## Owns / links

| Owns | Links to | Because |
|---|---|---|
| The OS/device/architecture matrix, minimums, degradation, deprecation | `library_compatibility` | the same matrix discipline applied to library versions |
| Permission and lifecycle behavior | `platform_permissions` | owned there, linked not restated |
