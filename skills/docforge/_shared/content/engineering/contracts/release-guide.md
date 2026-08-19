# `release-guide`

**Reader question** — "How do I cut a release, and what do I do if it needs to be rolled back?"

| Mode | Depth | Shape |
|---|---|---|
| How-to | deep-dive | executable-procedure |

## Must present

| # | Element | At | Done wrong |
|---|---|---|---|
| 1 | Prerequisites | L0 | a prerequisite discovered mid-procedure |
| 2 | One verified path, in order: version bump (with the versioning scheme and what triggers major/minor/patch), build, verification, publication, rollback | L1 | version bump triggers left unstated |
| 3 | Each command's observable success signal | L2 | a command with no checkable outcome |
| 4 | Rollback given equal weight to publication | L3 | rollback reduced to an afterthought paragraph |

## Keep out

| Not here | Lives in |
|---|---|
| Changelog content | `changelog` |
| Publishing mechanics for a specific artifact | `library_publishing` |

## Owns / links

| Owns | Links to | Because |
|---|---|---|
| The release procedure: gates, versioning, verification, rollback | `changelog` | the record of what was released is owned there |
| The success-signal discipline | `setup_guide` | each command is followed by its observable signal, the same discipline |
