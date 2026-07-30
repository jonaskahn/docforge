# Persistence writing craft

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

## Illustration

- **Form:** an `erDiagram` when entity relationships need it; a table for
  entity-to-storage mapping otherwise.
- **Renders:** durable relationships between entities (ER diagram), or the
  mapping from entity to storage representation (table).
- **Trigger:** the `erDiagram` only past two or more related entities whose
  relationship matters — per
  [`illustration.md`](../../../references/illustration.md)'s 8-entity limit.

## Connections

| This document owns | Links to | Because |
|---|---|---|
| Entities, storage mapping, migrations, transactions, consistency, failure recovery | `architecture-low-level` | the component that owns each entity is named there; this document owns the entity's storage contract |
| Entity field/schema definitions | the owning schema/reference document | never repeated inline |
| A state machine that uses this storage | `state-management` | state-management owns the lifecycle; this document owns the durability mechanics beneath it |
