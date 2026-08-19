# `architecture_compact`

**Reader question** — "How is this system built, and where does its structure meet its hard bounds and known debt?"

| Mode | Depth | Shape |
|---|---|---|
| Orientation | orientation | merged-section-spine |

At Spine every section here is Orientation/Explanation; the Diligence-only sections (whitebox decomposition, constraints, dependencies, tech debt) are Explanation/Reference internally, stated in each section's own lead, not in this facets row.

## What this file merges

| Member | At |
|---|---|
| `architecture_index` | spine |
| `arch_high_level` | spine |
| `arch_low_level` | diligence |
| `architecture_constraints` | diligence |
| `dependencies` | diligence |
| `tech_debt` | diligence |
| `system_overview` | spine (`multi_flow_repo`) |
| `ai_integration` | spine + ai-ml |
| `app_lifecycle` | spine + mobile-app, desktop-app |
| `app_ui_state` | spine + mobile-app, desktop-app |
| `contract_system` | spine + smart-contract |
| `data_flow` | spine + data-pipeline |
| `firmware_lifecycle` | spine + embedded-iot |
| `game_assets` | spine + game |
| `gameplay_systems` | spine + game |
| `hardware_map` | spine + embedded-iot |
| `host_integration` | spine + plugin-extension |
| `infra_environments` | spine + infrastructure-platform |
| `infra_network` | spine + infrastructure-platform |
| `model_lifecycle` | spine + ml-system |
| `persistence` | spine + persistence |
| `platform_integration` | spine + mobile-app, desktop-app |
| `pwa_installation` | spine + pwa |
| `web_components` | spine + website, web-app |
| `web_rendering` | spine + website, web-app |
| `web_state` | spine + website, web-app |
| `worker_triggers` | spine + worker-serverless |
| `data_contracts_index` | spine + data-pipeline |
| `dataset` (one section per discovered dataset) | spine + data-pipeline (`discovered_dataset`) |

## Must present

| # | Element | At | Done wrong |
|---|---|---|---|
| 1 | Section introduction: the system mental model | lead | component-level detail promoted into the lead |
| 2 | At-a-glance system mental model | `## At a glance` | detail a member section owns |
| 3 | Scope and boundaries, linking every unmerged document in this folder | `## Scope and boundaries` | a link to an unmaterialized path |
| 4 | High-level architecture: structure, boundaries, integration surfaces | `## High-level architecture` | component detail inside this section |
| 5 | At Diligence: whitebox decomposition with one intra-block runtime scenario | `## Whitebox decomposition` | duplicating the high-level map inside this section |
| 6 | At Diligence: hard constraints with design implication | `## Constraints` | a hard constraint restated inside the tech-debt section |
| 7 | At Diligence: the dependency inventory | `## Dependencies` | operational-failure framing owned by tech-stack, restated here |
| 8 | At Diligence: the tech-debt register | `## Tech debt` | a user-visible limitation filed as tech debt |
| 9 | Every profile- or shape-gated member section that was actually selected, each carrying its own contract's fields in full | `## {{Member}}` | a shape-gated member appearing when its selector was never evidenced |

## Keep out

| Not here | Lives in |
|---|---|
| Component-level detail a member contract reserves for its own document | that member's own section |
| Invented architecture not grounded in source | nowhere — omit rather than invent |
| Direct source-file navigation | provenance |
| User-visible limitations inside tech debt | `limitations` |

## Owns / links

| Owns | Links to | Because |
|---|---|---|
| Section introduction, at-a-glance, scope, and every selected member's content | every unmerged document in `docs/architecture/` | the fold covers the tier- and profile-selected members only; the rest keep their own paths |
| Nothing a folded member owns beyond hosting it | `architecture.md#<section anchor>` | a folded member has no file of its own; its contract's own links resolve inside this file |
