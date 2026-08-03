# Diligence-index writing craft

Each evidence cell links to a member document or repository-relative source path,
not merely an area name. For every partial or unsupported claim, state a concrete
follow-up and its evidenced owner token or `undetermined`; never promote it to a
verdict without support.

One row per claim under review: the claim, the evidence found for it, a
confidence level, and the gap remaining if confidence is anything less than
high. State confidence honestly on a small, fixed scale (for example
confirmed / partial / unsupported) rather than a prose hedge that dodges
the question. A claim with no evidence gets "unsupported" and a follow-up
action, not a soft rewrite into something the evidence happens to support.

Group by the area under diligence (architecture, security, operations,
dependencies) so a reader assessing one dimension doesn't have to scan the
whole table. Never render a verdict — pass/fail, safe/unsafe — this
document maps evidence and gaps.

## Illustration

- **Form:** a table is the whole document — this is an evidence map, not a
  narrative.
- **Renders:** nothing beyond the table; no diagram, ever.
- **Trigger:** never — per
  [`../../references/illustration.md`](../../references/illustration.md).

## Connections

| This document owns | Links to | Because |
|---|---|---|
| Claim, evidence, confidence, gap, grouped by diligence area | every member repo's own architecture/security/operations documents | each claim's evidence traces to a specific member document; this document maps, never restates, that evidence |
| An unresolved gap in repository discovery | `repo-inventory` | a claim about a repository that isn't fully inventoried traces its gap there |
| — | never a verdict of its own | pass/fail judgment belongs to the reader, not to this document |
