# `deployment`

**Reader question** — "How does an artifact actually get from build to a running environment, and how do I know it worked?"

| Mode | Depth | Shape |
|---|---|---|
| How-to | deep-dive | entry-catalog |

## Must present

| # | Element | At | Done wrong |
|---|---|---|---|
| 1 | One entry per environment: artifact source, rollout mechanism, rollback | per entry | environment differences re-derived instead of referenced to `infra_environments` |
| 2 | The rollout strategy stated plainly (blue-green, canary, rolling) | per entry | a rollout strategy left unnamed |
| 3 | A verification signal after every step | per entry | a step with no checkable outcome |

## Keep out

| Not here | Lives in |
|---|---|
| Incident procedures | `infra_disaster_recovery`, the relevant `runbook` |
| Environment value differences, re-derived | `infra_environments` |

## Owns / links

| Owns | Links to | Because |
|---|---|---|
| Environments' artifact path, rollout, rollback, verification | `infra_environments` | which values differ per environment is owned there, referenced not re-derived |
| Incident diagnosis and recovery | `infra_disaster_recovery` or the relevant `runbook` | recovery from a bad deploy is owned there, never embedded here |
