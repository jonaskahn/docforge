# `ba_compact`

**Reader question** — "What business rules and processes does this system implement, and what evidence backs each one?"

| Mode | Depth | Shape |
|---|---|---|
| Reference | deep-dive | merged-section-spine |

## What this file merges

| Member | At |
|---|---|
| `ba_index` | spine + business-analysts |
| `ba_process_flows` | spine + business-analysts |
| `ba_business_rules` | spine + business-analysts |
| `ba_requirements` | spine + business-analysts |

Every section is written in business language: a reader who does not read code must be able to follow it end to end.

## Must present

| # | Element | At | Done wrong |
|---|---|---|---|
| 1 | Section introduction: what a business analyst can find here | lead | a raw call chain standing in for a business narrative |
| 2 | At-a-glance process shape | `## At a glance` | detail a member section owns |
| 3 | Scope and boundaries, linking every unmerged document in this folder | `## Scope and boundaries` | a link to an unmaterialized path |
| 4 | Process flows: actor, trigger, business-language steps, decision points, exceptions, outcome, owning flow link | `## Process flows` | technical implementation detail replacing the business narrative |
| 5 | Business rules: stable rule id, plain-language statement, trigger, outcome, exceptions, enforcement evidence | `## Business rules` | a rule inferred only from a symbol or function name |
| 6 | Requirements traceability: requirement, evidence, owning rule/flow, implementation, test, status | `## Requirements traceability` | an invented ticket identifier |

## Keep out

| Not here | Lives in |
|---|---|
| Raw call chains | `arch_low_level`, the underlying `flow` document |
| A business rule repeated across multiple flows | the rule's own row, linked from each flow |
| Direct source-file navigation | provenance |

## Owns / links

| Owns | Links to | Because |
|---|---|---|
| Section introduction, at-a-glance, scope, process flows, business rules, and requirements traceability | each process flow's canonical `flow` document | the BA view links back to the technical flow rather than restating its steps |
| Nothing a folded member owns beyond hosting it | `business-analyst.md#<section anchor>` | a folded member has no file of its own; its contract's own links resolve inside this file |
