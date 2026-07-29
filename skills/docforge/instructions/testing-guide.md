# Testing-guide writing craft

**Preferred illustration:** Follow
[`../references/illustration.md`](../references/illustration.md); prose and
commands per layer, table only for the layer-comparison overview.

Organize by test layer — unit, integration, end-to-end — a rough test
pyramid: fast and narrow at the top of the document, slow and broad at the
bottom, matching how a contributor should actually reach for them. Give
each layer its own run command, what it covers, what it deliberately does
not cover, and its isolation model (does it hit a real database, a
container, a mock) — a layer description with no isolation model leaves a
contributor guessing whether a failure means their code or their
environment.

Close with failure diagnosis: what a flaky-looking failure in each layer
usually means, and the first thing to check — the how-to discipline
(Diataxis) applied to "my tests are red," not generic testing philosophy.
