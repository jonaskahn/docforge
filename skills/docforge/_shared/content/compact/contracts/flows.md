# `flows_compact`

**Reader question** — "What kinds of work does this system perform end to end, and which flow do I follow first?"

| Mode | Depth | Shape |
|---|---|---|
| Explanation | orientation | merged-section-spine |

## What this file merges

| Member | At |
|---|---|
| `flows_index` | spine |
| `flow` (one section per discovered flow) | diligence (`discovered_flow`) |

The candidate matrix comes first, holding every discovered flow whether or not it earned a written-up section; the section budget bounds how many are expanded here, never how many are known.

## Must present

| # | Element | At | Done wrong |
|---|---|---|---|
| 1 | Section introduction: what work this system performs, which flow to read first | lead | a table of contents in prose |
| 2 | At-a-glance flow shape: the areas work moves through | `## At a glance` | detail a folded section owns |
| 3 | Scope and boundaries, naming adjacent sections and linking every unmerged document in this folder | `## Scope and boundaries` | a promised link to an unmaterialized path |
| 4 | The complete candidate matrix: entry reference, area, confidence, reach, priority, status — every candidate, expanded or not | `## Flow candidate matrix` | dropping deferred rows, so coverage stops being stated |
| 5 | Per folded flow: its v3 reader question, guarantee before mechanism, exact adaptive section order, selected modules, diagram questions, terminal outcomes, residual state, recovery, and evidence gaps | `## {{Flow name}}` | a fixed happy-path/failures shell or default sequence diagram |
| 6 | Every evidenced obligation of the `flow` contract, repeated blocks collapsed to one line per instance, analysis order kept, nothing nested past `##` | `## {{Flow name}}` | summarized, not condensed: a folded flow that lost a selected module, failure branch, or gap |

## Keep out

| Not here | Lives in |
|---|---|
| A speculative flow with no evidence row | nowhere — it is not a candidate |
| A deferred candidate written up as if analyzed | the matrix, status `matrix only` |
| A flow whose index row is not `analysis_state: ready` | the v3 analysis and cold-review phase |
| An implementation walkthrough of a single function | `arch_low_level` |
| Direct source-file navigation | provenance |
| Business rule definitions | `ba_business_rules` |

## Owns / links

| Owns | Links to | Because |
|---|---|---|
| Section introduction, at-a-glance flow shape, scope, and the complete candidate matrix | every unmerged document in `docs/flows/` | the fold covers main-priority flows only; the rest keep their own paths |
| Nothing a folded flow owns | `flows.md#<slug>` anchors | a folded flow has no file of its own; the `flow` contract's own links resolve inside this file |
