# Gameplay-systems / assets-and-scenes writing craft

Covers `gameplay_systems` and `game_assets` — system boundaries and the
scenes/assets they load are described together in most engines and read
better linked than duplicated.

**Preferred illustration:** Follow
[`../references/illustration.md`](../references/illustration.md); prose
per system, table for scene/asset loading order.

For gameplay systems: state each system's boundary (what it owns, what it
doesn't) and its save-state contract — what persists across sessions and
how. For assets and scenes: state loading order and dependencies between
scenes, and the platform-build variance where asset pipelines differ by
target. Keep design-document aspiration out; describe what's implemented,
not the vision for it.
