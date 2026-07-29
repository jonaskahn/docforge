# Environments writing craft

**Preferred illustration:** Follow
[`../references/illustration.md`](../references/illustration.md); a table
with environment as columns is almost always the right shape.

State what actually differs between environments — configuration values,
scale, data realism, external service stubs — as a comparison table, one
row per dimension, environments as columns; a reader should be able to spot
every difference in one scan. State the promotion boundary as plainly:
what must be true before a change moves from one environment to the next,
and who owns that gate.

State configuration ownership per environment — which team or system
controls each environment's config — so a reader knows where to change a
value rather than guessing. Keep deployment procedure out; this document
describes what differs, [deployment.md](deployment.md) describes how to
ship into it.
