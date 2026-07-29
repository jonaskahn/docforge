# Persistence writing craft

**Preferred illustration:** Follow
[`../references/illustration.md`](../references/illustration.md); an
`erDiagram` when entity relationships need it (bounded per
illustration.md's 8-entity limit), a table for entity-to-storage mapping
otherwise.

Map each entity to its storage representation — table/collection name, key
strategy, and any denormalization that departs from the obvious mapping,
stated with the reason. State the migration mechanism (tool, versioning
scheme, whether migrations are reversible) as a fact, not a tutorial on the
tool itself. State the transaction and consistency boundary explicitly:
what operations are atomic together, and what consistency model applies
across entities that aren't (eventual, read-your-writes, none) — a
persistence document that never says "these two writes are not atomic" is
hiding the fact a reader most needs before building on top of it.

Close each entity or subsystem with its failure-recovery behavior — what
happens to a write in flight during a crash — using the same
absence-based-fact discipline architecture-low-level.md asks for
invariants ("never partially applies a multi-entity write").
