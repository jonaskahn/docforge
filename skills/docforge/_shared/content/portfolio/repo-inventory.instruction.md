# Repo-inventory writing craft

For every discovered member, record relative path, membership evidence, explicit
inclusion or exclusion decision and reason, pre-review baseline, work performed,
and remaining gap. Include role and owner only when directly supported; preserve
`undetermined` and link unresolved ownership to `diligence-index`.

One row per discovered repository: its role in the portfolio, an owner token
(team or individual accountable for it), documentation state (undocumented,
spine, diligence, portfolio-aware), and the evidence for each field — where
`discover_child_repos` or the manifest actually found this repository, not a
hand-typed addition. A row with no evidence is a defect; every repository
listed must trace to a discovery mechanism this document can name.

Never fill a gap with a plausible guess. If a repository's role or owner is
undetermined, state "undetermined" and let `diligence-index` carry the
resulting confidence gap — this document is the exhaustive lookup, not the
place judgment calls get resolved.

## Illustration

- **Form:** a Markdown table only — this is a Reference-depth lookup, not a
  narrative.
- **Renders:** nothing beyond the table; no relationship diagram, even when
  repositories depend on each other — that belongs to `system-context`.
- **Trigger:** never — per
  [`../../references/illustration.md`](../../references/illustration.md),
  reference documents default to tables.

## Connections

| This document owns | Links to | Because |
|---|---|---|
| Discovered repositories, role, owner token, documentation state, evidence | `system-context` | dependency and boundary relationships between repos are owned there; this document owns only the flat inventory |
| A gap in a repository's evidence | `diligence-index` | confidence and follow-up gaps are tracked there, not resolved here |
| A repository's own documentation tier | that repository's own `docs/INDEX.md` | this document names the tier; the repository's own docs are the source of truth for their content |
