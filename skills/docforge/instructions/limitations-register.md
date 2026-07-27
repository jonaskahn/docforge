# Limitations Register — Instruction Template

Craft guidance for writing `docs/reference/limitations.md`.
Content contract (must-present, keep-out, Diátaxis mode) and the tech-debt/constraint/limitation
litmus: `references/document-catalog.md` → "reference/limitations.md" and `references/risk-docs.md`.
Depth: `references/depth-and-audience.md`.

## Purpose
Record known constraints, unsupported scenarios, and hard bounds a user should know about.

## Data Requirements
- Knowledge graph (required)
- Direct inspection (TODO/FIXME comments, hard-coded bounds)
- Git history (when a limitation was identified)

## Template Structure
Group by category (functional, performance, scale, known issues). Per limitation:
- What it is — specific and measurable, not vague.
- Impact: what the reader can't do / what happens.
- Workaround, if one exists.
- Tracked in: link to the issue tracker if there is one.
- Root cause: a brief why, from code/architecture context.

## Provenance Requirements
- Tag each limitation with its code locations (TODO/FIXME, config constants).
- Record git blob hashes of the hard-coded bounds or checks behind it.
- Reference architecture/tech-debt.md for debt items that inform a limitation.

## Notes
- This is a trust document — be honest and specific. "Might have issues" is not a limitation.
- Limitations are by-design boundaries; internal shortcuts go in tech-debt.md, unfixable external
  boundaries in constraints.md (see the litmus in risk-docs.md).
