# `error-catalog`

**Reader question** — "This call returned this code — what does it mean, and should I retry?"

| Mode | Depth | Shape |
|---|---|---|
| Reference | reference | entry-catalog |

A caller's decision path, not a taxonomy: each code exists so a client can decide what to do next, not to classify implementation detail.

## Must present

| # | Element | At | Done wrong |
|---|---|---|---|
| 1 | The response envelope, stated once: which fields clients may branch on, which are human-facing or additive | lead | the envelope restated per code instead of once |
| 2 | Per code: stable anchor, trigger, observable status/category, safe client behavior, retryability, correlation/observability guidance | the catalog | a retryable claim unsupported by actual behavior |
| 3 | A closing status-level summary of the complete failure surface | L3 | no summary, leaving coverage unstated |

## Keep out

| Not here | Lives in |
|---|---|
| Stack traces, internal exception names, secrets | nowhere — never expose implementation internals |
| A renamed code treated as prose cleanup | nowhere — it is a compatibility change |
| The operation surface itself | `api_reference` |
| Rate-limit mechanics for the 429 code | `api_rate_limits` |

## Owns / links

| Owns | Links to | Because |
|---|---|---|
| The response envelope, code semantics, retryability, status summary | `api_reference` | endpoints restate the envelope once here and link to it |
| The 429 contract's headers and backoff facts | `api_rate_limits` | rate-limit mechanics are owned there |
