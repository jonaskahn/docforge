# Offline-installation writing craft

- Ground install and cache behavior in manifests, service-worker or cache
  configuration, implementation, and offline test evidence.
- Mark untested offline/reconnect behavior as unknown and link freshness
  guarantees to their data-flow owner.
- State installability criteria first (what makes the app installable at
  all), then the cache lifecycle: what's cached, when the cache updates, and
  how a stale cache is invalidated.
- State the offline boundary explicitly — what works with no network, what
  degrades, what fails outright — and the recovery behavior when
  connectivity returns.
- Avoid a generic service-worker tutorial; describe this app's actual
  caching strategy.

## Illustration

- **Form:** a Mermaid `stateDiagram-v2` for cache/update lifecycle states.
- **Renders:** named cache states (fresh, stale, updating, invalidated) and
  what triggers each transition.
- **Trigger:** once the cache lifecycle has more than a linear happy path —
  per
  [`illustration.md`](../../../references/illustration.md)'s deep-dive budget
  (at most 8 named states).

## Connections

| This document owns | Links to | Because |
|---|---|---|
| Installability, cache/update lifecycle, offline boundaries, invalidation, recovery | `application-lifecycle` | app-level launch/background states are owned there; this document owns the cache/network dimension specifically |
| A data staleness guarantee | `dataset` or `data-flow`, if the cached data has an owning contract elsewhere | avoids restating a freshness guarantee already owned by the data document |

## Voice

- **Voice:** declarative present tense, strong active verbs, no hedging.
