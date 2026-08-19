# Glossary / portfolio-glossary writing craft

Covers both `glossary` (repository-scoped) and `portfolio_glossary`
(cross-repo) — same litmus, different scope.

- One term, one precise definition, one link to the document that owns
  deeper explanation of it. If a term means something different in casual
  team usage than in the code, define the code's meaning and note the
  discrepancy in one clause; don't silently pick one.
- For the portfolio scope: include only terms that mean something across
  multiple member repos, or that would confuse a reader moving between
  them; a term local to one repo belongs in that repo's own glossary, not
  here. Link each portfolio entry to the clearest member-repo definition
  rather than restating it.
- Admit a term only when it is ambiguous, domain-specific, or stable
  project vocabulary that a reader needs to interpret another document.
  Link its evidence and canonical owner.
- When usage differs across code, teams, or repositories, record scoped
  variants and link each source; do not manufacture one canonical meaning.
- If no owner exists, state that boundary rather than expanding the
  glossary into a concept document.

## Illustration

- **Form:** an alphabetical table is the whole document.
- **Renders:** nothing beyond the table; a glossary never earns a diagram.
- **Trigger:** never — per
  [`../../references/illustration.md`](../../references/illustration.md).

## Linking craft

Name the owning document by what it owns, not by its filename: "the concept's
full model lives there," never "see `concept.md`." What each glossary entry
owns and why it links rather than restates is each contract's
`## Owns / links` table, not this section.
