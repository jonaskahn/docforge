# `access`

**Reader question** — "Who or what can change this infrastructure, and how was that access granted?"

| Mode | Depth | Shape |
|---|---|---|
| Reference | reference | lookup |

## Must present

| # | Element | At | Done wrong |
|---|---|---|---|
| 1 | One row per grant: principal, scope, grant path (a role, a policy — not just "IAM") | lead | a credential or literal access key instead of the mechanism name |
| 2 | Review cadence per grant, or an explicit `unknown` | L2 | silence read as "permanent," when that wasn't stated |

## Keep out

| Not here | Lives in |
|---|---|
| Credentials or secret values | nowhere — name the mechanism, never the value |
| Member-repo RBAC inventories unrelated to infra apply | the member repo's own access document |
| Resource inventory | `infra_resources` |

## Owns / links

| Owns | Links to | Because |
|---|---|---|
| Principals, scopes, grant paths, review cadence | `infra_resources` | a grant does not prove current resource state, and vice versa; kept as separate lookups |
