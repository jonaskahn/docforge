# `resources`

**Reader question** — "What infrastructure resources does this project manage, and who owns each one?"

| Mode | Depth | Shape |
|---|---|---|
| Reference | reference | lookup |

_Aliased with: `infrastructure-apply`, `infrastructure-state` (same content contract)._

## Must present

| # | Element | At | Done wrong |
|---|---|---|---|
| 1 | One row per managed resource: name, type, owner, criticality | the table | ordering alphabetically instead of by criticality |
| 2 | A stable locator or context per resource (account, environment, region, or canonical address) and a source-of-truth link | the table | mutable state or apply procedure copied instead of linked |

## Keep out

| Not here | Lives in |
|---|---|
| A credential or unverified destructive command | nowhere — never present an unverified destructive command as safe |
| Plan/apply procedure and recorded state | `infra_apply`, `infra_state` |
| Access grants | `infra_access` |

## Owns / links

| Owns | Links to | Because |
|---|---|---|
| The resource inventory | `dependencies` | the same criticality ordering principle for dependency rows |
| — | `infra_apply`, `infra_state` | this document lists resources; those own applying and recording state |
| — | `infra_access` | a resource does not prove who can use it, kept as a separate lookup |
