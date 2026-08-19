# `compatibility`

**Reader question** — "Which versions of this library or platform does it actually run on, tested?"

| Mode | Depth | Shape |
|---|---|---|
| Reference | reference | coverage-matrix |

The matrix table is the whole document: full coverage means every version this project claims support for, ordered newest first, each with its test evidence and deprecation horizon stated.

## Must present

| # | Element | At | Done wrong |
|---|---|---|---|
| 1 | Supported versions/platforms, ordered newest-version-first | the matrix | alphabetical or oldest-first ordering |
| 2 | Test evidence per row (CI matrix, manual verification, community report) | the matrix | "supported" claimed with no evidence basis |
| 3 | Deprecation behavior: when support for an older version ends, and what happens after | the matrix | an untested version marked compatible by default instead of unknown |

## Keep out

| Not here | Lives in |
|---|---|
| Migration procedure between two versions | `migration` |
| OS/device/architecture minimums | `platform_compatibility` |

## Owns / links

| Owns | Links to | Because |
|---|---|---|
| The supported library-version matrix and deprecation horizon | `migration` | the path between two specific versions is owned there |
| — | `platform_compatibility` | the same tested-evidence discipline applies at OS/device level |
