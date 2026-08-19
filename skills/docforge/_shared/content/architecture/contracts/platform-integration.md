# `platform-integration`

**Reader question** — "Which OS services does this app integrate with, and what happens when one is unavailable?"

| Mode | Depth | Shape |
|---|---|---|
| Explanation | deep-dive | entry-catalog |

## Must present

| # | Element | At | Done wrong |
|---|---|---|---|
| 1 | One section per OS service or platform adapter: what it's used for | per integration | a generic platform-API tutorial instead of this repository's actual usage |
| 2 | The permission boundary it requires, linked to `platform_permissions` rather than repeated | per integration | permission scope repeated instead of linked |
| 3 | The callback contract | per integration | a callback contract left implicit |
| 4 | Failure/fallback behavior when the service is unavailable | per integration | an unproven permission scope assumed instead of marked unknown |

## Keep out

| Not here | Lives in |
|---|---|
| A generic platform-API tutorial | nowhere |
| Permission rationale and scope | `platform_permissions` |
| A host-product (not OS) integration surface | `host_integration` |
| A lifecycle transition affected by a platform callback | `app_lifecycle` |

## Owns / links

| Owns | Links to | Because |
|---|---|---|
| OS services, adapters, permissions boundary, callbacks, failure and fallback | `platform_permissions` | permission rationale and scope is owned there; this document only names which permission each integration requires |
| A host-product (not OS) integration surface | `host_integration` | keeps host-product extension points distinct from OS/runtime adapters |
| A lifecycle transition affected by a platform callback | `app_lifecycle` | avoids re-deriving app lifecycle states here |
