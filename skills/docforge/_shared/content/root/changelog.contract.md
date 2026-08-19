# `changelog`

**Reader question** — "What changed between the version I have and the one I'm moving to?"

| Mode | Depth | Shape |
|---|---|---|
| Reference | reference | entry-catalog |

## Must present

| # | Element | At | Done wrong |
|---|---|---|---|
| 1 | The entry envelope: every released version carries a version number and release date | lead | an entry with no date |
| 2 | Compatibility changes, migrations, security fixes, and required actions, ordered before general enhancements within an entry | per entry | a breaking change buried under routine enhancements |
| 3 | Material user-visible changes only, translated from history — not every commit | per entry | a refactor, test change, or dependency bump listed with no behavior change |
| 4 | A link to the owning guide when a change needs procedure depth | per entry | migration steps written out in the changelog itself |

## Keep out

| Not here | Lives in |
|---|---|
| Unreleased or aspirational items | nowhere — wait for the release |
| A merged-but-unshipped change presented as released | nowhere — infer a release from a tag, never from a commit |
| The product-facing narrative of released impact | `release-notes` |
| Migration or versioning procedure | `migration`, `api_versioning` |

## Owns / links

| Owns | Links to | Because |
|---|---|---|
| Released versions, dates, user-visible changes, compatibility notes | `release-notes` | the product-facing view of released impact is owned there |
| A change needing procedure depth | the owning guide (`migration`, `api_versioning`) | linked, never embedded |
