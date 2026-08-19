# `infrastructure-state`

**Reader question** — "Where does this infrastructure's state actually live, and what happens when it drifts?"

| Mode | Depth | Shape |
|---|---|---|
| Reference | deep-dive | lookup |

_Aliased with: `infrastructure-apply`, `resources` (same content contract)._

## Must present

| # | Element | At | Done wrong |
|---|---|---|---|
| 1 | Where state lives, the locking mechanism that prevents concurrent writers, and who owns it | lead | a locking mechanism left unstated |
| 2 | How drift is detected | L2 | drift detection left implicit |
| 3 | The recovery procedure when actual infrastructure diverges from recorded state | L2 | a recovery procedure invented instead of linked to the authoritative tool procedure |

## Keep out

| Not here | Lives in |
|---|---|
| A credential | nowhere |
| An unverified destructive command | nowhere |
| The authorized actor and plan/apply gate | `infra_apply` |
| Resource inventory and access grants | `infra_resources`, `infra_access` |

## Owns / links

| Owns | Links to | Because |
|---|---|---|
| Backend, locking, state owner, drift detection, recovery | `infra_apply` | the authorized actor, gate, and execution boundary are owned there |
| Resource inventory and access grants | `infra_resources`, `infra_access` | owned in the reference documents, never restated here |
