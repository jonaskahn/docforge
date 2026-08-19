# `offline-installation`

**Reader question** — "What works with no network, and what happens when connectivity comes back?"

| Mode | Depth | Shape |
|---|---|---|
| Explanation | deep-dive | answer-first |

Installability criteria come first, before the cache lifecycle and offline boundary.

## Must present

| # | Element | At | Done wrong |
|---|---|---|---|
| 1 | Installability criteria: what makes the app installable at all | L0 | a generic service-worker tutorial instead of this app's actual strategy |
| 2 | The cache lifecycle: what's cached, when it updates, how a stale cache is invalidated | L1 | cache lifecycle stages left unstated |
| 3 | The offline boundary: what works with no network, what degrades, what fails outright | L2 | untested offline/reconnect behavior presented as fact instead of unknown |
| 4 | Recovery behavior when connectivity returns | L2 | recovery behavior omitted |

## Keep out

| Not here | Lives in |
|---|---|
| A generic service-worker tutorial | nowhere |
| App-level launch/background states | `app_lifecycle` |
| A cached data's freshness guarantee, if owned elsewhere | `dataset` or `data_flow` |

## Owns / links

| Owns | Links to | Because |
|---|---|---|
| Installability, cache/update lifecycle, offline boundaries, invalidation, recovery | `app_lifecycle` | app-level launch/background states are owned there; this document owns the cache/network dimension specifically |
| A data staleness guarantee | `dataset` or `data_flow`, if the cached data has an owning contract elsewhere | avoids restating a freshness guarantee already owned by the data document |
