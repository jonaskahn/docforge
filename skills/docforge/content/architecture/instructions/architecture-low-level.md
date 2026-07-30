# Low-level architecture writing craft

**Preferred illustration:** Follow
[`../../../references/illustration.md`](../../../references/illustration.md); use an ASCII
layered stack for static decomposition or a Mermaid sequence diagram for
cross-component order.

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
