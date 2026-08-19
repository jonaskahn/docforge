# `concepts_compact`

**Reader question** — "What domain concepts does this codebase use, and what does each one actually mean here?"

| Mode | Depth | Shape |
|---|---|---|
| Explanation | deep-dive | merged-section-spine |

## What this file merges

| Member | At |
|---|---|
| `concepts_index` | diligence |
| `concept` (one section per discovered concept) | diligence (`discovered_concept`) |

The concept register comes first, holding every discovered concept whether or not it earned a written-up section; the section budget bounds how many are explained in full here.

## Must present

| # | Element | At | Done wrong |
|---|---|---|---|
| 1 | Section introduction: what this vocabulary register is | lead | a glossary-style definition standing in for a concept's model |
| 2 | The concept register: concept, where it is defined in code, which documents depend on it | `## Concept register` | dropping a discovered concept from the register because it lacks a section |
| 3 | Scope and boundaries, linking every unmerged document in this folder | `## Scope and boundaries` | a link to an unmaterialized path |
| 4 | Per folded concept: what it models, its owning block, lifecycle and states, invariants stated as rules, relationships to neighbouring concepts, failure boundary, where it lives | `## {{Concept name}}` | a neighbouring concept's invariants folded into this one |
| 5 | Every field of the `concept` contract, repeated blocks collapsed to one line per instance, contract level order kept | `## {{Concept name}}` | summarized, not condensed: a folded concept that lost its invariants or failure boundary |

## Keep out

| Not here | Lives in |
|---|---|
| A concept with no definition in the repository | nowhere — it is not a candidate |
| A term that is only a glossary entry | `glossary` |
| A rule an architecture section owns | `arch_high_level`, `arch_low_level` |
| Direct source-file navigation | provenance |

## Owns / links

| Owns | Links to | Because |
|---|---|---|
| Section introduction, scope, the concept register, and every folded concept's content | every unmerged document in `docs/concepts/` | the fold covers concepts only; the rest keep their own paths |
| Nothing a folded concept owns | `concepts.md#<slug>` anchors | a folded concept has no file of its own; the `concept` contract's own links resolve inside this file |
