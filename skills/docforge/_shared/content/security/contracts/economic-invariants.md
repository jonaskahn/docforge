# `economic-invariants`

**Reader question** — "What must always hold true about this contract's economics and authority, and where's the boundary that could break it?"

| Mode | Depth | Shape |
|---|---|---|
| Explanation | deep-dive | entry-catalog |

_Aliased with: `contract-system` (same content contract)._

## Must present

| # | Element | At | Done wrong |
|---|---|---|---|
| 1 | Contracts, storage layout, authorities, and networks in scope | lead | a contract or authority omitted from the inventory |
| 2 | The upgrade boundary: what can change, and under whose authority | L2 | an upgrade path with no stated authority |
| 3 | Economic and security invariants, each stated as a rule that must always hold | L2 | an invariant stated as current behavior rather than a rule |

## Keep out

| Not here | Lives in |
|---|---|
| An unsupported audit verdict | nowhere — cite the actual audit or state none exists |
| Deployment procedure | `network_deployment` |

## Owns / links

| Owns | Links to | Because |
|---|---|---|
| Contracts, storage, authorities, networks, invariants | `network_deployment` | deployment mechanics are owned there, linked not restated |
