# `network-deployment`

**Reader question** — "How does a contract actually get deployed to this network, and who holds the privileged roles?"

| Mode | Depth | Shape |
|---|---|---|
| How-to | deep-dive | entry-catalog |

## Must present

| # | Element | At | Done wrong |
|---|---|---|---|
| 1 | One entry per target network (mainnet, testnet, or equivalent) | lead | one generic procedure covering multiple networks without naming which |
| 2 | Per network, in order: network configuration, key/role setup, deploy, post-deploy verification | per entry | account or multisig control inferred instead of evidenced |
| 3 | Privileged roles (deployer, admin, upgrader) as a table: who holds which, and what each can do | per entry | a deployment procedure with no named privileged roles |
| 4 | Upgrade and rollback given the same rigor as the initial deploy | per entry | rollback reduced to an afterthought |

## Keep out

| Not here | Lives in |
|---|---|
| A private key, seed phrase, or fabricated address | nowhere — use an obviously synthetic placeholder and say so |
| The upgrade-boundary standard itself | `economic_invariants` |
| Plan/apply gates for the rest of infrastructure | `infra_apply`, `infra_state` |

## Owns / links

| Owns | Links to | Because |
|---|---|---|
| Per-network deploy, upgrade, rollback, privileged roles | `economic_invariants` | the upgrade-boundary standard is owned there |
| — | `infra_apply`, `infra_state` | the same safety discipline, owned there |
