# Concept writing craft

- One concept, one document.
- Open by naming the concept and the responsibility it owns in a single
  sentence — what would break, or who would be confused, if this concept did
  not exist.
- Trace its relationships next: what it depends on, what depends on it, and
  the boundary at which its responsibility ends and a neighboring concept's
  begins.
- State its invariants as things that must always be true, not as
  descriptions of current behavior — a reader should be able to tell the
  difference between "this is how it works today" and "this must never
  change without breaking a caller's assumption."
- Close with the failure boundary: what this concept guarantees will not
  happen, and what it explicitly does not protect against.
- Never walk the reader through the concept symbol by symbol; that tour
  belongs to the code itself, not to a document meant to outlive a refactor.

## Illustration

- **Form:** prose for a single relationship or two; a small Mermaid
  `flowchart` only once three or more related concepts need their boundaries
  shown together.
- **Renders:** the concept as one node among its immediate dependencies and
  dependents — never the concept's internal structure.
- **Trigger:** only when relationships, not the concept itself, are hard to
  hold in the reader's head in prose — per
  [`illustration.md`](../../../references/illustration.md)'s deep-dive budget.

## Connections

| This document owns | Links to | Because |
|---|---|---|
| This concept's responsibility, relationships, invariants | `architecture-high-level` (the block it belongs to) | the concept is the deep-dive version of one block named there |
| — | `architecture-low-level` | low-level traces the mechanism that implements this concept's invariants |
| A shortcut affecting this concept | `tech-debt-register` | fixable-by-us shortcuts are never described here as if permanent |
| A hard bound affecting this concept | `constraints` | externally imposed limits are owned there, not repeated per concept |

## Voice

- **Voice:** declarative present tense, strong active verbs, no hedging.
