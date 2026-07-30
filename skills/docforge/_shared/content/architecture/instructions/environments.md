# Environments writing craft

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

## Illustration

- **Form:** a Markdown table with environments as columns — almost always
  the right shape for a comparison of this kind.
- **Renders:** every dimension that differs (config, scale, data realism,
  service stubs) across environments, one row each.
- **Trigger:** never for a diagram — this is a reference-adjacent lookup
  per [`illustration.md`](../../../references/illustration.md).

## Connections

| This document owns | Links to | Because |
|---|---|---|
| Environment differences, promotion boundaries, configuration ownership | `operations` deployment/runbook documents | this document says what differs; deployment procedure (how to ship into an environment) is owned there |
| Configuration values themselves | `reference/configuration` | this document owns which team controls config per environment, not the values or their schema |
