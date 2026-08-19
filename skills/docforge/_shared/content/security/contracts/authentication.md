# `authentication`

**Reader question** — "How does a caller authenticate, and what happens when their credential is missing, expired, or revoked?"

| Mode | Depth | Shape |
|---|---|---|
| Reference | deep-dive | entry-catalog |

_Aliased with: `api-reference`, `rate-limits` (same content contract)._

## Must present

| # | Element | At | Done wrong |
|---|---|---|---|
| 1 | The scheme named by its real category (API key, bearer token, OAuth2 grant type, mTLS, signed request) | lead | a scheme left unnamed or vaguely described |
| 2 | Per scheme, the credential lifecycle in order: issued, transmitted, rotated, then expiry/revocation | per scheme | lifecycle stages given out of order or incomplete |
| 3 | A failure-mode table: missing/expired/revoked credential, wrong scope — each with status code and caller action | the table | scattered prose instead of a table |
| 4 | Scope-to-capability mapping, as data | the table | a paragraph the caller must parse to find one scope |

## Keep out

| Not here | Lives in |
|---|---|
| A real credential, secret, or token value, even as an example | nowhere — use an obviously synthetic placeholder |
| A hand-copied generated schema | nowhere — derive from the source |
| The public surface itself | `api_reference` |
| Quota contracts | `api_rate_limits` |
| Shared error contracts | `api_errors` |

## Owns / links

| Owns | Links to | Because |
|---|---|---|
| The public surface and compatibility boundary | `api_reference` | the schema or generator that defines it is owned there |
| Quota contracts | `api_rate_limits` | owned there, linked not restated |
| Shared error contracts | `api_errors` | owned there, linked not restated |
