# `reference_compact`

**Reader question** — "What can I look up about this system's settings, API, stack, and known limits?"

| Mode | Depth | Shape |
|---|---|---|
| Reference | reference | merged-section-spine |

## What this file merges

| Member | At |
|---|---|
| `reference_index` | spine |
| `configuration` | spine |
| `limitations` | spine |
| `tech_stack` | spine |
| `glossary` | diligence |
| `api_reference` | spine + api-service, library-sdk |
| `api_errors` | spine + api-service |
| `api_rate_limits` | spine + api-service |
| `cli_commands` | spine + cli-tui |
| `cli_output` | spine + cli-tui |
| `extension_points` | spine + plugin-extension |
| `library_compatibility` | spine + library-sdk |
| `data_types` | spine + data-pipeline |
| `model_card` | spine + ml-system |
| `browser_support` | spine + website, web-app |
| `platform_compatibility` | spine + mobile-app, desktop-app, game |
| `performance_budgets` | spine + game, embedded-iot |
| `infra_resources` | spine + infrastructure-platform |
| `infra_access` | spine + infrastructure-platform |

## Must present

| # | Element | At | Done wrong |
|---|---|---|---|
| 1 | Section introduction: what a reader can look up here | lead | narrative connective tissue between lookup subjects |
| 2 | At-a-glance reference coverage | `## At a glance` | detail a member section owns |
| 3 | Scope and boundaries, linking every unmerged document in this folder | `## Scope and boundaries` | a link to an unmaterialized path |
| 4 | Configuration reference, limitations register, technology stack | `## Configuration`, `## Limitations`, `## Tech stack` | a lookup subject this section does not own, folded in anyway |
| 5 | At Diligence: the repository glossary | `## Glossary` | a glossary entry that restates a definition owned elsewhere instead of linking |
| 6 | Every profile-gated member section that was actually selected, each carrying its own contract's fields in full | `## {{Member}}` | a fact a member contract keeps out, folded in anyway |

## Keep out

| Not here | Lives in |
|---|---|
| A fact a member contract keeps out | that member's own document |
| Direct source-file navigation | provenance |

## Owns / links

| Owns | Links to | Because |
|---|---|---|
| Section introduction, at-a-glance, scope, and every selected member's content | every unmerged document in `docs/reference/` | the fold covers the tier- and profile-selected members only; the rest keep their own paths |
| Nothing a folded member owns beyond hosting it | `reference.md#<section anchor>` | a folded member has no file of its own; its contract's own links resolve inside this file |
