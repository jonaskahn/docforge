# `data-flow`

**Reader question** — "As this data moves from producer to consumer, what does each stage guarantee, and what happens on failure?"

| Mode | Depth | Shape |
|---|---|---|
| Explanation | deep-dive | entry-catalog |

_Aliased with: `data-quality`, `data-types` (same content contract)._

## Must present

| # | Element | At | Done wrong |
|---|---|---|---|
| 1 | One lineage per section: producer, each transformation in order, every consumer | per lineage | an unbounded diagram of everything that touches the data instead of the named lineage |
| 2 | Per transformation, what it guarantees about its output (schema, ordering, completeness) as a contract, not an implementation description | per lineage | an implementation description instead of a downstream contract |
| 3 | The schema's owning document named at each handoff, never repeated inline | per lineage | field definitions repeated instead of linked |
| 4 | Failure and recovery per traced flow: what happens to in-flight data on a stage failure | per lineage | a lineage diagram with only the happy-path story |

## Keep out

| Not here | Lives in |
|---|---|
| Unevidenced lineage or a sample-only guarantee | nowhere — label it unknown |
| Field definitions, repeated inline | the owning schema/reference document |
| Business logic already owned by a flow | the triggering `flow` document |

## Owns / links

| Owns | Links to | Because |
|---|---|---|
| Producer, each transformation, every consumer, per-handoff guarantees, failure/recovery | `dataset` | dataset owns the data's contract at rest; this document owns its movement and transformation |
| Field definitions at each handoff | the owning schema/reference document | never repeated inline; name the owner and link |
| A rule enforced during a transformation | the flow document that triggers this pipeline, if one exists | avoids re-deriving business logic already owned by a flow |
