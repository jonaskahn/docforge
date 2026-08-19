# `versioning`

**Reader question** — "What breaks my integration if I don't pin a version, and when does a deprecated version actually stop working?"

| Mode | Depth | Shape |
|---|---|---|
| Reference | reference | answer-first |

The versioning scheme is the governing claim, stated before any specific deprecation.

## Must present

| # | Element | At | Done wrong |
|---|---|---|---|
| 1 | The versioning scheme: what changes without a version bump, what forces one | L0 | a deprecation listed before the scheme is explained |
| 2 | How a caller pins a version (header, path segment, account default) | L1 | the pinning mechanism left unstated |
| 3 | Per deprecation, the same three facts in order: deprecated-in version, stops-working version/date, replacement | L2 | "not yet scheduled" omitted instead of stated plainly |
| 4 | Deprecations ordered by how soon they bite | L2 | alphabetical ordering |

## Keep out

| Not here | Lives in |
|---|---|
| Changelog content | `changelog` |
| An unverified future version or date | nowhere |
| Operation-level request/response detail | `api_reference` |

## Owns / links

| Owns | Links to | Because |
|---|---|---|
| The versioning scheme, compatibility promise, deprecation facts | `api_reference` | operation-level request/response detail is owned there, linked not restated |
