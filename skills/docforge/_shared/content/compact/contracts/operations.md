# `operations_compact`

**Reader question** — "How does this system get deployed and observed, and what do I run when something breaks?"

| Mode | Depth | Shape |
|---|---|---|
| Explanation | orientation | merged-section-spine |

## What this file merges

| Member | At |
|---|---|
| `operations_index` | diligence |
| `deployment` | diligence |
| `observability` | diligence |
| `distribution` | spine + mobile-app, desktop-app, cli-tui, plugin-extension, game |
| `flashing_recovery` | spine + embedded-iot |
| `infra_apply` | spine + infrastructure-platform |
| `infra_disaster_recovery` | spine + infrastructure-platform |
| `infra_state` | spine + infrastructure-platform |
| `network_deployment` | spine + smart-contract |
| `worker_reliability` | spine + worker-serverless |
| `runbooks_index` | diligence |
| `runbook` (one section per discovered runbook) | diligence (`discovered_runbook`) |

The runbook register comes with the fold: every discovered runbook keeps a row whether or not it earned a section.

## Must present

| # | Element | At | Done wrong |
|---|---|---|---|
| 1 | Section introduction: how this system is deployed and operated | lead | provider marketing standing in for operational fact |
| 2 | At-a-glance operational shape | `## At a glance` | detail a member section owns |
| 3 | Scope and boundaries, linking every unmerged document in this folder | `## Scope and boundaries` | a link to an unmaterialized path |
| 4 | Deployment: environments, artifact path, rollout, rollback, verification | `## Deployment` | a rollout with no stated rollback |
| 5 | Observability: signals, ownership, correlation, alert intent, blind spots | `## Observability` | a blind spot left unstated |
| 6 | The runbook register, and one section per folded runbook carrying trigger, verified steps, and recovery outcome | `## Runbooks` | a register-only runbook written up as though its procedure had been verified |

## Keep out

| Not here | Lives in |
|---|---|
| Provider marketing | nowhere — state the verified capability only |
| An unverified runbook procedure | the register, status unverified |
| Direct source-file navigation | provenance |

## Owns / links

| Owns | Links to | Because |
|---|---|---|
| Section introduction, at-a-glance, scope, deployment, observability, and the runbook register with its folded sections | every unmerged document in `docs/operations/` | the fold covers the tier- and profile-selected members only; the rest keep their own paths |
| Nothing a folded member owns beyond hosting it | `operations.md#<section anchor>` | a folded member has no file of its own; its contract's own links resolve inside this file |
