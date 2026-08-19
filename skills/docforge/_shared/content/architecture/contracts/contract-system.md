# `contract-system`

**Reader question** — "What contracts does this system deploy, who can call their privileged functions, and how can they change?"

| Mode | Depth | Shape |
|---|---|---|
| Explanation | deep-dive | entry-catalog |

_Aliased with: `economic-invariants` (same content contract)._

## Must present

| # | Element | At | Done wrong |
|---|---|---|---|
| 1 | Every contract, named, with its storage layout at the level a reader needs (not a field-by-field dump) | per contract | a field-by-field storage dump |
| 2 | Which authorities can call privileged functions, and which network(s) it's deployed to | per contract | authority or network claims with no deployment or governance evidence |
| 3 | The upgrade boundary, stated plainly: immutable, proxy-upgradeable, or governance-gated | per contract | an unsupported audit verdict ("this contract is safe") |

## Keep out

| Not here | Lives in |
|---|---|
| An unsupported audit verdict | nowhere — state evidence and accepted residual risk instead |
| A private key or fabricated address | nowhere — placeholders only |
| Economic/security invariants themselves | `economic_invariants` |

## Owns / links

| Owns | Links to | Because |
|---|---|---|
| Contract, network, storage, authority, and upgrade inventory | `economic_invariants` | the paired view; inventory rows link to invariants, never restate them |
| Accepted residual risk and audit evidence | `threat_model` | the same evidence-and-residual-risk discipline is owned there |
