# Gameplay systems

_Last reviewed: {{YYYY-MM-DD}}_

_Repeat per system — the `##` block below._

## {{System, e.g. Combat}}

**Owns:** {{responsibility}} · **Does not own:** {{boundary}}

**Update order:** {{where this system falls in the event/update sequence
relative to others it depends on}}

**Save-state contract:** {{what persists across sessions, and how}}

**On incompatible save:** {{behavior when a save predates this system's
current data shape — migrate, reset, or reject}}

Scenes and assets: see [assets-and-scenes.md](assets-and-scenes.md).
