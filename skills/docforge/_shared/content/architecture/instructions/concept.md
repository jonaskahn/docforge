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

## Level discipline

Ordered per
[`progressive-disclosure.md`](../../../references/progressive-disclosure.md).

| Level | Sections |
|---|---|
| L0 — answer | the opening sentence and the block this concept belongs to |
| L1 — shape | `## What it models`, `## Lifecycle and states` |
| L2 — detail | `## Invariants`, `## Relationships`, `## Failure boundary` |
| L3 — boundary | `## Where it lives` |

Name every state before explaining what holds at any one of them. An invariant
that only applies in one state is stated under `## Invariants` with the state
named, never smuggled into the lifecycle prose.

## Illustration

Two conditional views; a concept document commonly earns neither, and that is a
correct outcome rather than a gap.

| View | Form | Renders | Trigger |
|---|---|---|---|
| Lifecycle | Mermaid `stateDiagram-v2` | the states this concept moves through and what moves it between them | three or more states with at least one non-linear transition; ordered prose below that |
| Neighbourhood | Mermaid `flowchart` | the concept as one node among its immediate dependencies and dependents — never its internal structure | three or more related concepts whose boundaries must be seen together |

Both are bounded by
[`illustration.md`](../../../references/illustration.md)'s deep-dive budget (a
state diagram at most 8 named states). Draw neither when prose holds the
relationships comfortably: the trigger is the reader's difficulty, not the
document's length.

## Connections

| This document owns | Links to | Because |
|---|---|---|
| This concept's responsibility, relationships, invariants | `architecture-high-level` (the block it belongs to) | the concept is the deep-dive version of one block named there |
| — | `architecture-low-level` | low-level traces the mechanism that implements this concept's invariants |
| A shortcut affecting this concept | `tech-debt-register` | fixable-by-us shortcuts are never described here as if permanent |
| A hard bound affecting this concept | `constraints` | externally imposed limits are owned there, not repeated per concept |

## Voice

- **Voice:** declarative present tense, strong active verbs, no hedging.
