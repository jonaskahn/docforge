# `portfolio-glossary`

**Reader question** — "What does this term mean across the portfolio, when member repos might define it differently?"

| Mode | Depth | Shape |
|---|---|---|
| Reference | reference | lookup |

An alphabetical table is the whole document; an entry is admitted only when the term means something across multiple member repos or would confuse a reader moving between them.

## Must present

| # | Element | At | Done wrong |
|---|---|---|---|
| 1 | One row per admitted cross-repo term: term, precise definition, link to the clearest member-repo entry | the table | a term local to one repo padding the portfolio glossary |
| 2 | Scoped variants recorded and linked when usage differs across member repos, rather than one manufactured canonical meaning | the table | one canonical meaning invented to paper over real variation |

## Keep out

| Not here | Lives in |
|---|---|
| A term local to one repo | that repo's own `glossary` |
| Repository-local ADR duplication | the member repo's own `adr` |
| A restated definition instead of a link | nowhere — link the clearest member-repo entry |

## Owns / links

| Owns | Links to | Because |
|---|---|---|
| A portfolio-scoped term's precise definition | the clearest member-repo glossary entry | avoids re-defining a term the portfolio glossary only needs to disambiguate across repos |
