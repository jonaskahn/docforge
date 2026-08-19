# `platform-permissions`

**Reader question** — "What does this app ask permission for, and what happens if I say no or revoke it later?"

| Mode | Depth | Shape |
|---|---|---|
| Reference | deep-dive | entry-catalog |

## Must present

| # | Element | At | Done wrong |
|---|---|---|---|
| 1 | One entry per requested capability: the capability, its request trigger (first launch, first feature use, explicit settings action) | lead | a capability with no stated trigger |
| 2 | User-visible value unlocked, and denial behavior | per entry | a permission the reader cannot find declared anywhere in the manifest |
| 3 | The settings path to change the decision later, and behavior when a granted permission is revoked mid-session | per entry | a permission that silently breaks on revocation, left unsurfaced |

## Keep out

| Not here | Lives in |
|---|---|
| An invented entitlement, capability, or policy claim | nowhere — ground every entry in the manifest or platform declaration |
| Platform minimums and degradation | `platform_compatibility` |

## Owns / links

| Owns | Links to | Because |
|---|---|---|
| Requested capabilities, request timing, denial fallback, revocation recovery | `platform_compatibility` | platform minimums and degradation are owned there |
| The data a granted permission unlocks | `data_handling` | access boundaries per class are owned there |
