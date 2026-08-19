# `publishing`

**Reader question** — "How does an artifact actually get published, and how do I roll it back if it's bad?"

| Mode | Depth | Shape |
|---|---|---|
| How-to | deep-dive | executable-procedure |

## Must present

| # | Element | At | Done wrong |
|---|---|---|---|
| 1 | Prerequisites and artifact identity | L0 | a step that assumes an ungrounded prerequisite |
| 2 | One verified path, in order: version source, build/sign, registry/channel, verify, rollback/deprecate | L1 | steps given as a menu of alternatives instead of one path |
| 3 | Each step's observable success signal, immediately after it | L2 | a step with no checkable outcome |
| 4 | Rollback/deprecation given the same rigor as the happy path | L3 | rollback reduced to an afterthought paragraph |

## Keep out

| Not here | Lives in |
|---|---|
| A secret value (registry token, signing key) | nowhere — name the mechanism, never the value |
| Changelog content | `changelog` |
| The project's overall release procedure | `release_guide` |

## Owns / links

| Owns | Links to | Because |
|---|---|---|
| Artifact identity, gates, publish mechanics, rollback/deprecate | `release_guide` | the project's release procedure is owned there |
| What was published | `changelog` | the record is owned there, linked never restated |
