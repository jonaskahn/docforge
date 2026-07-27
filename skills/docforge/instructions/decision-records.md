# Decision Records — Instruction Template

Craft guidance for the ADR index and format under `docs/architecture/decisions/`.
Content contract (must-present, keep-out, Diátaxis mode) and the full ADR treatment:
`references/document-catalog.md` → "architecture/decisions/NNNN-<slug>.md — ADRs" and
`references/decision-records.md`. Depth: `references/depth-and-audience.md`.

## Purpose
Provide the ADR index and the template teams use to record architectural decisions already made.

## Data Requirements
- Git history (for existing / backfilled decisions)
- No other source requirements

## Template Structure
- Lead: "Architecture Decision Records (ADRs) capture major decisions made in this project,"
  and why recording them helps future contributors understand the trade-offs.
- Index table: # | Date | Title | Status (Accepted / Superseded / Deprecated).
- ADR template: Title & status; Context (the forces, value-neutral); Decision ("We will…");
  Rationale (why this, not the alternatives); Consequences (positive, negative *named*, neutral);
  Alternatives considered; Revisit trigger.

## Provenance Requirements
- ADRs live in `docs/architecture/decisions/` (numbered from 0001; the folder README is the index).
- Reference the git commits that introduced each decision.
- Cross-reference the architecture docs that explain the consequences.

## Notes
- ADRs are append-only — supersede, never rewrite an old one.
- Keep each to 1–2 pages; accessibility matters more than formal rigour.
- An ADR records a decision already made — not a forward design proposal.
- Prefer dating by commit or release over calendar date.
- Link from architecture/low-level.md sections that explain *why* a design was chosen.
