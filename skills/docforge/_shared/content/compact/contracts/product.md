# `product_compact`

**Reader question** — "What does this product do, who is it for, and what does it explicitly not do?"

| Mode | Depth | Shape |
|---|---|---|
| Orientation | orientation | merged-section-spine |

## What this file merges

| Member | At |
|---|---|
| `product_index` | spine |
| `product_overview` | spine |
| `quickstart` | spine + api-service, library-sdk |
| `api_versioning` | spine + api-service |
| `content_model` | spine + website |
| `accessibility` | spine + accessibility |
| `localization` | spine + localization |
| `library_migrations_index` | spine + library-sdk |
| `migration` | spine + library-sdk (`discovered_migration`) |

## Must present

| # | Element | At | Done wrong |
|---|---|---|---|
| 1 | Section introduction: what the product is and who it serves | lead | a feature list with no stated audience |
| 2 | At-a-glance product mental model | `## At a glance` | detail a member section owns |
| 3 | Scope and boundaries, linking every unmerged document in this folder | `## Scope and boundaries` | a link to an unmaterialized path |
| 4 | Product overview: users, problems, capabilities, explicit non-goals | `## Product overview` | an invented roadmap item or implementation detail |
| 5 | Every field of each selected member's own contract, condensed never summarized | `## {{Member}}` | a shape-gated member appearing when its selector was never evidenced |

## Keep out

| Not here | Lives in |
|---|---|
| Child-owned facts beyond the overview | the owning member |
| Invented roadmap or implementation detail | nowhere — omit unless evidenced |
| Direct source-file navigation | provenance |

## Owns / links

| Owns | Links to | Because |
|---|---|---|
| Section introduction, at-a-glance, scope, product overview, and every selected member's content | every unmerged document in `docs/product/` | the fold covers the tier- and profile-selected members only; the rest keep their own paths |
| Nothing a folded member owns beyond hosting it | `product.md#<section anchor>` | a folded member has no file of its own; its contract's own links resolve inside this file |
