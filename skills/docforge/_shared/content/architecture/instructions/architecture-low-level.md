# Low-level architecture writing craft

This is C4's Component level (Level 3) — the zoom-in on the containers named in
high-level.md — so component boundaries here should trace back to a block named there, not
introduce a parallel decomposition. Organize by subsystem responsibility, not directory
traversal: a folder holding three unrelated responsibilities gets three write-ups, not one.

For each subsystem, explain inputs, state transitions, outputs, failure containment, and
adjacent dependencies in that order. Add a sequence diagram only when the reader must
follow who calls whom across components; use prose and a record-layout fence when the point
is the shape of data rather than call order. Skip the visual when prose alone does not force
a reader to reconstruct a multi-step interaction. Write invariants as absence-based facts a reader cannot
recover by reading code ("never retries a non-idempotent write") — the same discipline the
scaffold's own Invariant field asks for. Close each section with the stable file/module
paths that orient implementation work.

`arch_low_level` is a component zoom-in and must trace each component to a
high-level block. `concept` is a durable subsystem topic: define its
responsibility, relationships, invariant, and failure boundary without forcing
a parent-component decomposition. State only dependency semantics for data;
link persistence or datasets for their model and storage mechanics. For each
non-obvious failure, name evidence and the symptom or escalation boundary that
hands control to operations or another owner.

## Illustration

- **Form:** an ASCII layered stack for static decomposition; a Mermaid
  `sequenceDiagram` for cross-component call order.
- **Renders:** the component grouping and its boundaries (ASCII), or the
  one architecturally relevant runtime scenario across components (sequence).
- **Trigger:** the sequence diagram only when a reader must follow a
  multi-step interaction across components — per
  [`illustration.md`](../../../references/illustration.md)'s deep-dive budget
  (at most 5 participants).

## Connections

| This document owns | Links to | Because |
|---|---|---|
| Module/component responsibilities, one representative runtime scenario, data/control paths, failure boundaries | `architecture-high-level` (as parent zoom level) | every component here must trace to a block named there — no parallel decomposition |
| A specific persisted entity or dataset touched by a component | `persistence` or `dataset` | storage mechanics are owned there; this document only names the dependency |
| A rule this component enforces on request/response shape | `reference` (API/config) | the observable contract is owned by the reference document; this document explains the mechanism behind it |
