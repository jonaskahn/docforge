# `infrastructure-apply`

**Reader question** — "Who can run apply, what gates it, and what happens when it fails or drifts?"

| Mode | Depth | Shape |
|---|---|---|
| Reference | deep-dive | lookup |

_Aliased with: `infrastructure-state`, `resources` (same content contract)._

## Must present

| # | Element | At | Done wrong |
|---|---|---|---|
| 1 | The authorized actor and the gate between plan and apply (review, approval, CI check) | lead | apply authority left unstated |
| 2 | Preflight, approved artifact, execution boundary, abort condition | L2 | a runnable command shown with no environment, mutability, or expected result |
| 3 | Every apply-adjacent command shown, safe to run against a real environment after reading the surrounding prose | L2 | an invented runnable path instead of a link to the authoritative tool procedure |

## Keep out

| Not here | Lives in |
|---|---|
| A credential | nowhere |
| An unverified destructive command | nowhere |
| Where state lives, locking, drift detection | `infra_state` |
| Resource inventory and access grants | `infra_resources`, `infra_access` |

## Owns / links

| Owns | Links to | Because |
|---|---|---|
| The plan/apply gate, execution boundary, abort condition | `network_deployment` | network-targeted deploys apply the same authority discipline |
| Resource inventory and access grants | `infra_resources`, `infra_access` | owned in the reference documents, never restated here |
