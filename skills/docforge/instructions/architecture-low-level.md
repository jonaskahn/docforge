# Low-level architecture writing craft

This is C4's Component level (Level 3) — the zoom-in on the containers named in
high-level.md — so component boundaries here should trace back to a block named there, not
introduce a parallel decomposition. Organize by subsystem responsibility, not directory
traversal: a folder holding three unrelated responsibilities gets three write-ups, not one.

For each subsystem, explain inputs, state transitions, outputs, failure containment, and
adjacent dependencies in that order. Use a sequence diagram when the reader needs to follow
who calls whom and in what order across two or more components; use a data-flow diagram
when the point is what shape the data takes as it moves, not who is calling whom. Skip the
diagram when prose alone doesn't force a reader to reconstruct a multi-step interaction —
not every subsystem earns one. Write invariants as absence-based facts a reader cannot
recover by reading code ("never retries a non-idempotent write") — the same discipline the
scaffold's own Invariant field asks for. Close each section with the stable file/module
paths that orient implementation work.
