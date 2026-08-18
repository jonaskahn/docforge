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
- Carry **both** C4 views as separate diagrams: a Context diagram in "System in
  context" and a Container diagram in "Building blocks". C4 recommends each of
  them for every software development team, and they answer different reader
  questions — who borders this system, then what runs inside it. One diagram
  standing in for both is the most common way this document ends up thinner
  than the prose it sits above.
- Name responsibilities with strong verbs ("owns," "validates," "routes"),
  not passive nouns ("handling," "management"). Put invariants in a visually
  distinct section.
- Keep the document stable by design: a claim a routine refactor would falsify
  is written too close to the code and belongs in low-level.md.
- Finish with links to low-level detail, decisions, and operational
  consequences. Name the forces that shaped this shape in one short paragraph —
  the constraint, the scale it was built for, the integration it had to live
  with — and link the record that settled each. The argument and the rejected
  alternatives stay in the decision record; a reader who never opens one should
  still know *why this shape*, which is what
  [`progressive-disclosure.md`](../../../references/progressive-disclosure.md)
  calls the document's L3 boundary.
- Order the document per that same reference: the capability at L0 before any
  structure, context and containers at L1, per-edge and per-boundary detail at
  L2, stability and rationale at L3.
- Every relationship is directional and uses a specific active verb. Name its
  protocol or channel when evidence establishes one; otherwise say `unknown`.
  Never combine the C4 Context and Container zooms in a single diagram — they
  are two diagrams, one per section.

## Illustration

Two views, one per section, each answering a different question. Splitting is
the remedy for density, never a violation: per
[`illustration.md`](../../../references/illustration.md), complexity goes into
more diagrams, never into a bigger one.

- **Form:** a Mermaid `flowchart` in each of the two sections.
- **Renders:** *context* — this system as one box among its neighbors, naming
  each neighbor and the contract between them, never an internal;
  *containers* — the deployable blocks inside that box and how they
  communicate, each labeled with its implementing technology.
- **Trigger:** context, always. Containers, whenever more than one deployable
  block exists — which is every repository that ships more than a single
  process. The container table beside it stays: it carries technology,
  interface, boundary, and routing columns the diagram cannot.
- **Decomposed in column:** the container table's routing column, not a third
  diagram — coherence (illustration.md) rules out spending another picture on
  "where do I go to see inside this block" when a table cell answers it at
  zero illustration cost. Name the low-level whitebox that decomposes that
  block, or `—` when it has none.
- **Budget:** the orientation bound applies per diagram, not per document. If
  either view exceeds it, split by business or functional area rather than
  dropping the view.

## Connections

| This document owns | Links to | Because |
|---|---|---|
| Context, blocks, boundaries, communication, invariants | `architecture-low-level` | low-level is this document's zoom-in; a block named here must trace to a component write-up there |
| — | `records/` (decisions) | rationale for why a block is shaped this way lives in decisions, never restated here |
| — | `tech-debt-register`, `constraints` | known shortcuts and hard bounds are tracked in their own registers, not folded into this stable document |
| Each deployable block's implementing technology | `reference/tech-stack` | what the repository is built with is owned there; this document only labels each block with it |

## Voice

- **Voice:** declarative present tense, strong active verbs, no hedging.
