# `migration`

**Reader question** — "I'm on version X, moving to version Y — what breaks, and in what order do I fix it?"

| Mode | Depth | Shape |
|---|---|---|
| How-to | deep-dive | executable-procedure |

## Must present

| # | Element | At | Done wrong |
|---|---|---|---|
| 1 | Source and target versions, stated in the opening line | L0 | a migration guide written with no evidenced source-to-target transition |
| 2 | Breaking changes listed in the order a reader must apply them | L1 | changelog sequence substituted for application order |
| 3 | Per breaking change: exact before/after, and the search-and-replace or codemod where mechanical | L2 | a manual step presented as verified mechanical work |
| 4 | A closing verification step, and a rollback path or an explicit statement that none exists | L3 | rollback omitted with no statement that none exists |

## Keep out

| Not here | Lives in |
|---|---|
| The full version-support matrix | `library_compatibility` |
| An unverified manual step presented as mechanical | nowhere — distinguish them |

## Owns / links

| Owns | Links to | Because |
|---|---|---|
| The source→target migration path, breaking changes, verification, rollback | `library_compatibility` | the full version-support matrix is owned there; this document is the path between two versions |
