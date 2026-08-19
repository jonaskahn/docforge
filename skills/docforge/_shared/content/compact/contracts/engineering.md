# `engineering_compact`

**Reader question** — "How is this repository built, tested, and released?"

| Mode | Depth | Shape |
|---|---|---|
| Explanation | orientation | merged-section-spine |

## What this file merges

| Member | At |
|---|---|
| `engineering_index` | spine |
| `setup_guide` | spine |
| `testing_guide` | spine |
| `conventions` | diligence (`conventions_source`) |
| `release_guide` | diligence |
| `data_quality` | spine + data-pipeline |
| `library_publishing` | spine + library-sdk |
| `web_styling` | spine + website, web-app |

## Must present

| # | Element | At | Done wrong |
|---|---|---|---|
| 1 | Section introduction: how this repository is built and tested | lead | generic style advice with no repository evidence |
| 2 | At-a-glance engineering practices | `## At a glance` | detail a member section owns |
| 3 | Scope and boundaries, linking every unmerged document in this folder | `## Scope and boundaries` | a link to an unmaterialized path |
| 4 | Setup instructions, verified end to end | `## Setup` | a step with no checkable outcome |
| 5 | Testing instructions | `## Testing` | a test command that was never actually run |
| 6 | At Diligence: evidenced conventions, when a conventions source exists | `## Conventions` | a convention invented with no source |
| 7 | At Diligence: the release procedure | `## Release` | a release step the member contract keeps out |

## Keep out

| Not here | Lives in |
|---|---|
| Commands or rules a member contract keeps out | that member's own document |
| Generic style advice with no repository evidence | nowhere — omit rather than invent |
| Direct source-file navigation | provenance |

## Owns / links

| Owns | Links to | Because |
|---|---|---|
| Section introduction, at-a-glance, scope, and every selected member's content | every unmerged document in `docs/engineering/` | the fold covers the tier- and profile-selected members only; the rest keep their own paths |
| Nothing a folded member owns beyond hosting it | `engineering.md#<section anchor>` | a folded member has no file of its own; its contract's own links resolve inside this file |
