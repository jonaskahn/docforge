# `contributing_compact`

**Reader question** — "Who owns what in this repository, and how does a contributor find the right reviewer?"

| Mode | Depth | Shape |
|---|---|---|
| Reference | orientation | merged-section-spine |

## What this file merges

| Member | At |
|---|---|
| `contributing_index` | diligence |
| `ownership` | diligence |

The root `CONTRIBUTING.md` router stays a separate, always-present file; it is not a member of this group.

## Must present

| # | Element | At | Done wrong |
|---|---|---|---|
| 1 | Section introduction: how this section guides a contributor once they've read the root router | lead | restating the root router's contribution path |
| 2 | At-a-glance contribution path | `## At a glance` | detail owned by a member section |
| 3 | Scope and boundaries, linking every unmerged document in this folder | `## Scope and boundaries` | a link to an unmaterialized path |
| 4 | Owned areas with responsibility boundaries and escalation tokens | `## Ownership` | an invented person or team not evidenced in the repository |

## Keep out

| Not here | Lives in |
|---|---|
| Invented people or teams | nowhere — omit unless evidenced |
| Verified-checks detail | root `CONTRIBUTING.md` |
| Direct source-file navigation | provenance |

## Owns / links

| Owns | Links to | Because |
|---|---|---|
| Section introduction, at-a-glance, scope, and ownership boundaries | root `CONTRIBUTING.md` | the required-checks path lives there, not duplicated here |
| Nothing a folded member owns | `contributing.md#<section anchor>` | a folded member has no file of its own; its contract's own links resolve inside this file |
