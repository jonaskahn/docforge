# `po_compact`

**Reader question** — "What features shipped, how do we know they worked, and what's the evidence trail to the ticket?"

| Mode | Depth | Shape |
|---|---|---|
| Reference | deep-dive | merged-section-spine |

## What this file merges

| Member | At |
|---|---|
| `po_index` | spine + product-owners |
| `po_features` | spine + product-owners |
| `po_metrics` | spine + product-owners |
| `po_release_notes` | spine + product-owners |
| `backlog_traceability` | spine + product-owners (`ticket_evidence`) |

Backlog traceability appears only when the repository carries ticket evidence.

## Must present

| # | Element | At | Done wrong |
|---|---|---|---|
| 1 | Section introduction: what a product owner can find here | lead | an implementation inventory standing in for feature value |
| 2 | At-a-glance product shape | `## At a glance` | detail a member section owns |
| 3 | Scope and boundaries, linking every unmerged document in this folder | `## Scope and boundaries` | a link to an unmaterialized path |
| 4 | Feature catalog: user outcome, audience, availability, owning flow | `## Feature catalog` | internal refactor or dependency churn listed as a feature |
| 5 | Success metrics: outcome, measure, instrumentation state, interpretation, external target token | `## Success metrics` | an invented target with no external source |
| 6 | Release notes: released user impact, version/date, compatibility impact, feature links | `## Release notes` | an empty seed table left in place of an honest empty state |
| 7 | Backlog traceability, only when ticket evidence exists: evidenced ticket id, feature, flow/change, release/status link | `## Backlog traceability` | a guessed ticket mapping |

## Keep out

| Not here | Lives in |
|---|---|
| An implementation inventory | `arch_low_level` |
| An invented success target | nowhere — link the external source or omit the row |
| Internal refactor or dependency-bump noise | `changelog`, and only if user-visible |
| Direct source-file navigation | provenance |

## Owns / links

| Owns | Links to | Because |
|---|---|---|
| Section introduction, at-a-glance, scope, feature catalog, success metrics, release notes, and backlog traceability | each feature's owning `flow` document | the PO view links to the technical flow rather than restating its mechanism |
| Nothing a folded member owns beyond hosting it | `product-owner.md#<section anchor>` | a folded member has no file of its own; its contract's own links resolve inside this file |
