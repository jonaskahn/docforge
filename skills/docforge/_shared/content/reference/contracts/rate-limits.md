# `rate-limits`

**Reader question** — "How many requests can I make, and exactly what happens when I exceed that?"

| Mode | Depth | Shape |
|---|---|---|
| Reference | reference | lookup |

_Aliased with: `api-reference`, `authentication` (same content contract)._

## Must present

| # | Element | At | Done wrong |
|---|---|---|---|
| 1 | The limiting dimension stated first: per API key, per IP, per endpoint, per account tier | lead | the limiting dimension left implicit |
| 2 | Sustained rate vs. burst allowance, distinguished where both exist | the table | sustained and burst conflated into one number |
| 3 | The exact response contract: status code and every header the caller reads, named literally (`Retry-After`, remaining-quota headers, reset timestamp) | the table | "the appropriate header" instead of the literal header name |
| 4 | The 429 imperative: back off for the stated duration, then retry | L2 | a description ("clients should implement backoff") instead of an imperative |

## Keep out

| Not here | Lives in |
|---|---|
| A hand-copied generated schema or secret | nowhere |
| The operation surface itself | `api_reference` |
| Endpoint-specific authentication mechanism | `api_authentication` |
| The 429 code's machine-readable semantics | `api_errors` |

## Owns / links

| Owns | Links to | Because |
|---|---|---|
| Limit values by dimension, tiering, the 429 retry contract | `api_reference` | the surface these limits attach to is owned there; per-endpoint rate-limit classes are its columns |
| Endpoint-specific authentication | `api_authentication` | the auth mechanism is owned there, linked not restated |
| The 429 code's machine-readable semantics | `api_errors` | codes, triggers, and retryability are owned there |
