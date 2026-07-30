# Glossary / portfolio-glossary writing craft

Covers both `glossary` (repository-scoped) and `portfolio_glossary`
(cross-repo) — same litmus, different scope.

One term, one precise definition, one link to the document that owns
deeper explanation of it — a glossary entry that re-explains the concept
in full duplicates that owning document and will drift from it. If a term
means something different in casual team usage than in the code, define
the code's meaning and note the discrepancy in one clause; don't silently
pick one.

For the portfolio scope: include only terms that mean something across
multiple member repos, or that would confuse a reader moving between them;
a term local to one repo belongs in that repo's own glossary, not here.
Link each portfolio entry to the clearest member-repo definition rather
than restating it.

## Illustration

- **Form:** an alphabetical table is the whole document.
- **Renders:** nothing beyond the table; a glossary never earns a diagram.
- **Trigger:** never — per
  [`../../references/illustration.md`](../../references/illustration.md).

## Connections

| This document owns | Links to | Because |
|---|---|---|
| Term and its precise definition | the document that owns the concept in depth (e.g. a `concept` or `flow` document) | the glossary is a pointer, not an explanation — one owner per fact |
| A portfolio-scoped term | the clearest member-repo glossary entry | avoids re-defining a term the portfolio glossary only needs to disambiguate across repos |
