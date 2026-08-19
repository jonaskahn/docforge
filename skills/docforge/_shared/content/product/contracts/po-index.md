# `po-index`

**Reader question** — "What lives in this section, and which document here answers my question?"

Aliased with: `folder-index`, `docs-index`, `ba-index`, `portfolio-index`, `portfolio-decisions-index` (same content contract).

| Mode | Depth | Shape |
|---|---|---|
| Orientation | orientation | router |

A router introduces the section, orients the reader, bounds it, and hands off — it carries no fact a child owns.

## Must present

| # | Element | At | Done wrong |
|---|---|---|---|
| 1 | What this section is, why it exists, who should read it | L0 | restating the repository's purpose |
| 2 | The section-level mental model: the major topics and how they fit | L1 | a child's own detail promoted here |
| 3 | What belongs here, and which adjacent section owns the rest, named so a lost reader can leave | L1 | a boundary with no named neighbour |
| 4 | Reading paths by task or audience, linking only into children | L1 | a link into a source file |
| 5 | Every selected, materialized, non-agent-context child, each with the reader question it answers, most-orienting first | L2 | alphabetical order; a title restated as a purpose |
| 6 | For a folded child, the merged anchor (`<compact_target>#<slug or section anchor>`), never the unmaterialized standard path | L2 | linking `product/overview.md` when compact wrote `product.md#overview` |
| 7 | An honest empty state when no child is evidenced | L2 | a placeholder row naming a document that does not exist |
| 8 | The parent index and the sibling sections a reader is most likely to need next | L3 | a nested index linking more than one parent |

## Keep out

| Not here | Lives in |
|---|---|
| Commands, flow steps, rules, configuration, ADR rationale, failure analysis | the child that owns each |
| Any agent-context document, linked or mentioned | nowhere — permanently isolated |
| A link to an unselected or unwritten child | nowhere — omit until it is written |
| An illustration of its own | the child that needs it |

## Owns / links

| Owns | Links to | Because |
|---|---|---|
| Orientation only: introduction, at-a-glance, scope, reading paths, child map | every selected, materialized non-agent child | children own their facts; this file owns only the route |
| Nothing else | its parent index, if nested | keeps the router chain traceable from the repository root down |
