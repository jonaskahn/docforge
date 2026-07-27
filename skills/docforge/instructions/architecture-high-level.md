# Architecture High-Level — Instruction Template

Craft guidance for writing `docs/architecture/high-level.md`.
Content contract (must-present, keep-out, Diátaxis mode): `references/document-catalog.md`
→ "architecture/high-level.md — the stable map". Depth: `references/depth-and-audience.md`.

## Purpose
A system overview showing major blocks, boundaries, and how they interact — the stable map
everything else references.

## Data Requirements
- Knowledge graph (required) — module map, layers, edges
- Domain graph (optional) — business context

## Template Structure
- Open with a 1–2 sentence hook: what this system is.
- Use ASCII or embedded-SVG block diagrams; keep prose concise — the diagram does the explaining.
- Each block shows: name, responsibility, abstraction level. Aggregate to module level, never
  list every file.
- A reader should be able to redraw the box diagram from the prose alone.

## Provenance Requirements
- Tag each block/section with the source modules from the knowledge graph.
- Record git blob hashes of the modules forming each layer.
- Reference blocks by file/module path, e.g. "User API service (`src/api/user-service/`)".

## Notes
- Restrict to what changes once or twice a year; faster-churning detail belongs in low-level.md.
