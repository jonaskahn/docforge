# `glossary`

**Reader question** — "What does this repository mean by this term?"

| Mode | Depth | Shape |
|---|---|---|
| Reference | reference | lookup |

An alphabetical table is the whole document: the term is the key, and nothing precedes the table but the one line stating the ordering.

## Must present

| # | Element | At | Done wrong |
|---|---|---|---|
| 1 | One line naming the key (the term) and the ordering (alphabetical) | lead | a paragraph explaining what a glossary is |
| 2 | One row per admitted term, alphabetical: term, precise definition, owning-document link | the table | a term local to casual team usage presented as the code's meaning with no discrepancy noted |
| 3 | A term admitted only when ambiguous, domain-specific, or stable project vocabulary a reader needs to interpret another document | the table | a generic language term padding the table |

## Keep out

| Not here | Lives in |
|---|---|
| Duplicate flow or architecture prose | the concept or flow document that owns the term in depth |
| A definition with no owner | nowhere — state the boundary rather than expanding into a concept document |
| An illustration | nowhere — a glossary never earns a diagram |

## Owns / links

| Owns | Links to | Because |
|---|---|---|
| Term and its precise definition | the document that owns the concept in depth (e.g. `concept` or `flow`) | the glossary is a pointer, not an explanation — one owner per fact |
