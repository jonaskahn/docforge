# Gameplay-systems / assets-and-scenes writing craft

Covers `gameplay_systems` and `game_assets` — system boundaries and the
scenes/assets they load are described together in most engines and read
better linked than duplicated.

For gameplay systems: state each system's boundary (what it owns, what it
doesn't) and its save-state contract — what persists across sessions and
how. For assets and scenes: state loading order and dependencies between
scenes, and the platform-build variance where asset pipelines differ by
target. Keep design-document aspiration out; describe what's implemented,
not the vision for it.

## Illustration

- **Form:** prose per system; a table for scene/asset loading order.
- **Renders:** each system's boundary as a short paragraph; the loading
  sequence and its per-scene dependencies as a table.
- **Trigger:** the table once loading order involves more than two scenes
  or assets with dependencies between them — per
  [`illustration.md`](../../../references/illustration.md)'s deep-dive budget.

## Connections

| This document owns | Links to | Because |
|---|---|---|
| System boundaries, scenes/assets, loading, save state, platform builds | `architecture-high-level` | this is the deep-dive of the gameplay/asset block named there |
| A platform-specific asset pipeline difference | `platform-integration` | per-platform packaging/runtime detail is owned there |
| A known loading or save-state shortcut | `tech-debt-register` | a fixable shortcut is tracked there, not normalized into the description here |
