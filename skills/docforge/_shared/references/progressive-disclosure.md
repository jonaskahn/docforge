# Progressive disclosure

This reference owns **ordering**: the sequence in which a document reveals
detail. [`depth-and-audience.md`](depth-and-audience.md) owns how much detail a
document carries; this file owns what comes first. A document can hold exactly
the right facts at exactly the right depth and still fail its reader by putting
the answer last.

## The levels

Every substantive document moves through four levels in order. The levels are
not headings — each type's template owns its section names — they are the
altitude each section is written at.

| Level | Carries | The reader who stops here |
|---|---|---|
| **L0 — Answer** | What this is, what it produces, and what a reader can now rely on. One governing statement, before any mechanism. | Can decide whether this is the document they need, and can state the outcome correctly. |
| **L1 — Shape** | The whole subject in one pass, complete but shallow: the ordered steps, the container map, the register of parts. Every item named; no item explained. | Can describe the whole thing end to end and knows every part exists. What they learned is incomplete, never wrong. |
| **L2 — Detail** | Per-item depth: branch conditions, failure handling, component contracts, invariants, observability. | Has lost detail on the items below where they stopped, never a corrected understanding of the ones above. |
| **L3 — Boundary** | Where this document stops: what it deliberately does not cover, who owns the rest, and the rationale links. | Knows which document answers what they still want. |

## The rules

1. **Answer first.** The governing fact — the outcome, the guarantee, the
   capability the system owns — appears at L0, never only at the bottom. A
   reader must not have to reach the last section to learn what the subject
   produces.
2. **Complete before deep.** Name every item at L1 before explaining any item at
   L2. Never explain the first item fully and then introduce the second.
3. **Never mix levels.** An L1 section must not sprout L2 detail for one
   favoured item. If a step needs a paragraph, that paragraph belongs at L2
   under its own sub-heading. This is the prose form of the zoom-consistency
   rule [`illustration.md`](illustration.md) already applies to diagrams:
   detail that does not belong at this altitude goes to the next one, not into
   this one.
4. **Order by consequence.** Within L2, order items by how often they occur or
   by blast radius, most consequential first — not by code order, not
   alphabetically.
5. **Repeat the guarantee, nothing else.** The outcome may be stated at L0 and
   again in full at L3. That is the one licensed repetition; it exists because
   a reader who stops at L0 must still be correct. No other fact is restated —
   [`document-composition.md`](document-composition.md) still governs
   single-ownership everywhere else.

## The stop test

At every level boundary, ask: *a reader who stops reading here — is what they
now believe true, and is it enough to act on at this altitude?* If stopping
after L1 leaves a reader with a wrong impression rather than a partial one, the
ordering is broken: something at L2 is correcting L1 instead of extending it,
and the correction belongs higher.

This is the acceptance test the independent audit applies; see
[`document-audit.md`](document-audit.md).

## Scope

Applies to substantive documents — the ones that carry mechanism, at
`deep-dive` target depth and to the orientation documents that front them.

It does **not** apply to:

- **Reference documents.** A lookup table has no argument to order; its
  ordering is whatever makes a field findable. `reference` depth is exempt.
- **Routers and section READMEs.** These have their own instance of this rule,
  already stated as `## Top-down shape` in
  [`../content/shared/folder-index.instruction.md`](../content/shared/folder-index.instruction.md).
  That file governs them; this one does not restate it.
- **Agent-context outputs.** They are read by a machine in one pass, not
  skimmed. [`voice.md`](voice.md) already sets their shape.

## What this file does not decide

It sets no word counts and no section lengths. Level discipline is the lever;
length is not one. A document is not improved by growing a section, only by
putting the right altitude in it — and
[`depth-and-audience.md`](depth-and-audience.md)'s "promote rather than pad"
still holds.
