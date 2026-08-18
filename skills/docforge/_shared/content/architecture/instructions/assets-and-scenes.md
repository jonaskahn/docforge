# Assets-and-scenes writing craft

- Open with the system's boundaries: what counts as a scene or an asset in
  this engine/project, and where the loading pipeline's responsibility starts
  and ends.
- Trace loading next in the order it actually happens (discovery, load,
  instantiation, teardown), then save-state (what is captured, what is
  regenerated instead of saved, and why), then platform-build differences
  (what changes per target platform — asset formats, streaming behavior,
  memory budgets).
- Close with failure behavior: a missing asset, a corrupted save, or a load
  timeout, and whether the game fails safe, retries, or falls back to a
  placeholder.
- Do not drift into design-document territory — describe the loading and
  scene system as it behaves today, not the creative vision for what scenes
  should eventually contain.

## Illustration

- **Form:** an ASCII `text` block for the scene/asset directory or loading
  pipeline stages; a Mermaid `stateDiagram-v2` only if scene lifecycle has
  more than a linear load-to-teardown path.
- **Renders:** the loading pipeline as an ordered stack, or scene states and
  transitions if branching exists (paused, streaming, unloading).
- **Trigger:** the state diagram only past a linear happy path — per
  [`illustration.md`](../../../references/illustration.md)'s deep-dive
  budget.

## Connections

| This document owns | Links to | Because |
|---|---|---|
| System boundaries, scenes/assets, loading, save state, platform builds | `architecture-high-level` | this is the deep-dive of the asset/scene block named there |
| A platform-specific build difference | `platform-integration` | per-platform packaging/runtime detail is owned there; this document only notes that a difference exists |
| A known loading shortcut | `tech-debt-register` | a fixable shortcut in the pipeline is tracked there, not silently normalized here |

## Voice

- **Voice:** declarative present tense, strong active verbs, no hedging.
