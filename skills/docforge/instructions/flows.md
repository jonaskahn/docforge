# Business Flows — Instruction Template

Craft guidance for writing `docs/flows/<flow>.md` (and, once promoted, `<flow>/README.md`).
Content contract (must-present, keep-out, Diátaxis mode): `references/document-catalog.md`
→ "flows/<flow>.md". Flat-file-by-default and atomic-promotion rules: `references/document-composition.md`.
Depth: `references/depth-and-audience.md`.

## Purpose
Document the step-by-step execution of a key business process, in plain language.

## Order of work — main flows first
Write flows in **entry-point-centrality order**, not file order: the flows reached
from the application's entry points (routes/API handlers, then the highest-fan-out
services) are the main ones — document them before the long tail. `derive_flow_graph.py
prepare` ranks them for you (its `clusters`/`entryPoints` are already in this order,
`--max-flows` caps the main set); native sources are ranked the same way
(GitNexus `cross_community` processes first). See `references/domain-derivation.md`.

## Data Requirements
- Domain graph (REQUIRED — hard gate, no fallback to inspection; see SKILL.md)
- Knowledge graph (for implementation detail when a deep-dive subfile is written)

## Template Structure
For each flow:
- One-line summary of what the flow accomplishes.
- A numbered step list in sequence; for each step: what happens, which component(s) participate,
  success/failure branches.
- A Mermaid (or ASCII/SVG) diagram once the flow has more than one step or a branch.
- Reference the specific modules implementing each step.
Use clear numbered steps — readability before cleverness.

## Provenance Requirements
- Tag each step with the modules implementing it.
- Record which domain-graph nodes sourced each step.
- Cross-reference architecture/low-level.md sections that detail the mechanism.

## Notes
- A flow stays a flat `.md` until real per-reader depth is written; promote to a folder with
  business-analyst.md / engineering.md / product-owner.md subfiles only in the same pass their
  content is written — never a folder or "go deeper" link with no subfile behind it.
