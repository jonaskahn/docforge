# High-level architecture writing craft

- Ground every context, boundary, block, and invariant in code-graph or
  manifest evidence.
- Link implementation technology to `tech-stack`; mark an unproven boundary
  or technology choice as unknown rather than completing the diagram by
  inference.
- Map onto C4's top two levels: "System in context" is the Context diagram
  (this system as one box among the neighbors and services it borders);
  "Building blocks" is the Container diagram (the deployable pieces inside
  that box). Keep the zoom consistent within each section — never let a
  container-level block sprout component-level detail; that belongs in
  low-level.md.
- Open with a one-paragraph system frame: what this is, at the highest level,
  and the business capability it owns.
- Move from context to blocks to communication and boundaries in that order —
  a reader should be able to draw the box diagram from the prose alone.
- Add a visual only when it clarifies relationships among three or more blocks.
- Name responsibilities with strong verbs ("owns," "validates," "routes"),
  not passive nouns ("handling," "management"). Put invariants in a visually
  distinct section.
- Keep the document stable by design: a claim a routine refactor would falsify
  is written too close to the code and belongs in low-level.md.
- Finish with links to low-level detail, decisions, and operational
  consequences — rationale lives in decisions, not here.
- Every relationship is directional and uses a specific active verb. Name its
  protocol or channel when evidence establishes one; otherwise say `unknown`.
  Do not combine C4 Context and Container zooms in the one permitted
  orientation illustration.

## Illustration

- **Form:** a small Mermaid `flowchart` for context and container relationships.
- **Renders:** this system as one box among its neighbors (context), then its
  deployable blocks and their communication (containers) — never both zoom
  levels in the same diagram.
- **Trigger:** only when it clarifies relationships among three or more
  blocks — per
   [`illustration.md`](../../../references/illustration.md)'s orientation budget.

## Connections

| This document owns | Links to | Because |
|---|---|---|
| Context, blocks, boundaries, communication, invariants | `architecture-low-level` | low-level is this document's zoom-in; a block named here must trace to a component write-up there |
| — | `records/` (decisions) | rationale for why a block is shaped this way lives in decisions, never restated here |
| — | `tech-debt-register`, `constraints` | known shortcuts and hard bounds are tracked in their own registers, not folded into this stable document |
| Each deployable block's implementing technology | `reference/tech-stack` | what the repository is built with is owned there; this document only labels each block with it |
