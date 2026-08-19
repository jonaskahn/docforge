# `data-types`

**Reader question** — "What's the exact wire representation of this field, and can I implement against it?"

| Mode | Depth | Shape |
|---|---|---|
| Reference | reference | lookup |

_Aliased with: `data-flow`, `data-quality` (same content contract)._

## Must present

| # | Element | At | Done wrong |
|---|---|---|---|
| 1 | One row per type: name, wire representation, constraints, nullability | the table | "timestamp" instead of "ISO 8601 string, UTC" — not precise enough to implement against |
| 2 | Prior representation and the version it changed in, where a type was renamed or changed | the table | a representation change left unnoted |
| 3 | Types ordered by how often a reader looks them up | the table | alphabetical or internal-module ordering |

## Keep out

| Not here | Lives in |
|---|---|
| Business meaning reconstructed from a sample payload | nowhere — cite the schema, never a sample |
| Business rule semantics | `ba_business_rules` |
| Term definitions | `glossary` |

## Owns / links

| Owns | Links to | Because |
|---|---|---|
| Wire types, constraints, nullability, representation changes | `ba_business_rules`, `glossary` | business meaning is owned there, never reconstructed from a sample payload |
