# Offline-installation writing craft

**Preferred illustration:** Follow
[`../../../references/illustration.md`](../../../references/illustration.md); a
Mermaid `stateDiagram-v2` for cache/update lifecycle states.

State installability criteria first (what makes the app installable at
all), then the cache lifecycle: what's cached, when the cache updates,
and how a stale cache is invalidated. State the offline boundary
explicitly — what works with no network, what degrades, what fails
outright — and the recovery behavior when connectivity returns. Avoid a
generic service-worker tutorial; describe this app's actual caching
strategy.
