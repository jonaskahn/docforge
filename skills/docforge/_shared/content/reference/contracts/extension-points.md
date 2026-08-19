# `extension-points`

**Reader question** — "How does an extension attach to this host, and what can it actually do once attached?"

| Mode | Depth | Shape |
|---|---|---|
| Explanation | deep-dive | lookup |

_Aliased with: `host-integration` (same content contract)._

## Must present

| # | Element | At | Done wrong |
|---|---|---|---|
| 1 | The host contract and activation mechanism | lead | a host product tutorial standing in for the contract |
| 2 | Contribution points and the permissions each requires | L2 | a permission granted with no evidenced justification |
| 3 | Compatibility, sandbox boundaries, and failure behavior when the host rejects an extension | L2 | sandbox boundaries left unstated |

## Keep out

| Not here | Lives in |
|---|---|
| A host product tutorial | the host's own documentation, linked not reproduced |
| Marketplace or distribution procedure | `distribution` |

## Owns / links

| Owns | Links to | Because |
|---|---|---|
| Host contract, activation, contribution points, permissions, sandbox, failure | `distribution` | how the extension reaches a user is owned there |
