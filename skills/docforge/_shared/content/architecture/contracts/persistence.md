# `persistence`

**Reader question** — "How is this entity actually stored, and what happens to an in-flight write during a crash?"

| Mode | Depth | Shape |
|---|---|---|
| Explanation | deep-dive | entry-catalog |

## Must present

| # | Element | At | Done wrong |
|---|---|---|---|
| 1 | Each entity mapped to its storage representation: table/collection name, key strategy, denormalization with its reason | per entity | a denormalization with no stated reason |
| 2 | The migration mechanism (tool, versioning scheme, reversibility) stated as a fact, not a tutorial | per entity | a tutorial on the migration tool itself |
| 3 | The transaction and consistency boundary: what's atomic together, what consistency model applies otherwise | per entity | an unverified crash-recovery behavior presented as fact |
| 4 | Failure-recovery per entity, as absence-based facts ("never partially applies a multi-entity write") | per entity | a failure-recovery claim with no schema, migration, or code evidence |

## Keep out

| Not here | Lives in |
|---|---|
| Entity field/schema definitions, repeated inline | the owning schema/reference document |
| The component that owns each entity | `arch_low_level` |
| A state machine using this storage | `web_state` |

## Owns / links

| Owns | Links to | Because |
|---|---|---|
| Entities, storage mapping, migrations, transactions, consistency, failure recovery | `arch_low_level` | the component that owns each entity is named there; this document owns the entity's storage contract |
| Entity field/schema definitions | the owning schema/reference document | never repeated inline |
| A state machine that uses this storage | `web_state` | state-management owns the lifecycle; this document owns the durability mechanics beneath it |
