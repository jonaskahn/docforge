# `release-notes`

**Reader question** — "What changed in this release, and do I need to do anything about it?"

| Mode | Depth | Shape |
|---|---|---|
| Reference | reference | entry-catalog |

## Must present

| # | Element | At | Done wrong |
|---|---|---|---|
| 1 | One entry per release: what changed for users, whether they must act | per entry | a commit claimed as delivered with no release evidence |
| 2 | Which versions or clients are affected | per entry | compatibility, migration, security, or availability implications left implicit |
| 3 | A link to the owner document when a reader needs more than a summary | per entry | procedure detail duplicated instead of linked |

## Keep out

| Not here | Lives in |
|---|---|
| A refactor, test-only change, or dependency noise with no user-visible effect | nowhere — omit unless it materially changes behavior |
| The released-version record itself | `changelog` |

## Owns / links

| Owns | Links to | Because |
|---|---|---|
| Released user impact, version/date, compatibility implications | `changelog` | the released-version record is owned there |
| Affected capabilities | `po_features` | each changed feature is owned there |
| A compatibility or migration implication needing procedure depth | `api_versioning`, `migration` | the owning guide is linked, not summarized |
