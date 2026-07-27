# Tech Debt Register — Instruction Template

Craft guidance for writing `docs/architecture/tech-debt.md`.
Content contract (must-present, keep-out, Diátaxis mode) and the tech-debt/constraint/limitation
litmus: `references/document-catalog.md` → "architecture/tech-debt.md and architecture/constraints.md"
and `references/risk-docs.md`. Depth: `references/depth-and-audience.md`.

Scope: this file is for **tech-debt.md** only — internal, fixable-with-effort shortcuts. Hard
architectural limits the team cannot change are a **separate document** (`architecture/constraints.md`);
do not fold them in here. Use the litmus to route each item.

## Purpose
Record known technical debt and the workarounds currently in place, with repayment framing.

## Data Requirements
- Knowledge graph (for architecture context)
- Direct inspection (TODO/FIXME, comments explaining workarounds)
- Git history (when and why the debt was incurred)

## Template Structure
Organize by subsystem or priority. Per debt item:
- What the debt is (specific module/subsystem).
- Why it was incurred (deadline, trade-off, knowledge at the time).
- Current impact (what's harder/slower/riskier).
- Repayment cost estimate (effort, risk, dependencies) and any blockers.
- Suggested approach.

## Provenance Requirements
- Reference the specific files/modules containing the debt.
- Link the TODO/FIXME comments and the git commits that introduced it (with rationale from the message).

## Notes
- Tech debt is deliberate trade-off, not failure — be honest about the (often good) reasons.
- Don't soften language: "needs refactoring" beats "could be improved".
- List debt that actually slows new work; skip minor nits.
