# `host-integration`

**Reader question** — "What does this extend, how does an integration activate, and what happens when the host is incompatible?"

| Mode | Depth | Shape |
|---|---|---|
| Explanation | deep-dive | answer-first |

The host contract — what this extends, activation events, compatibility range — is the governing claim, stated before any single contribution point.

_Aliased with: `extension-points` (same content contract)._

## Must present

| # | Element | At | Done wrong |
|---|---|---|---|
| 1 | The host contract: what this extends, activation events, compatibility range with host versions | L0 | a generic "how extension systems work" tutorial instead of this repository's actual contract |
| 2 | Failure behavior when the host is incompatible or the extension crashes | L2 | an unsupported version or unobserved host behavior stated as fact instead of an explicit gap |
| 3 | The lifecycle explanation: activation, compatibility, sandbox, failure boundary | L2 | permission rationale duplicated instead of linked to security |

## Keep out

| Not here | Lives in |
|---|---|
| A generic extension-system tutorial | nowhere |
| The stable lookup surface (identifier, trigger, input/output, permission, compatibility per point) | `extension_points` |
| Permission rationale | `platform_permissions` |

## Owns / links

| Owns | Links to | Because |
|---|---|---|
| The host's place among neighbors and services | `arch_high_level` | the block this host extends is named there |
| Permission rationale per point | `platform_permissions` | owned in the security group, linked not duplicated |
