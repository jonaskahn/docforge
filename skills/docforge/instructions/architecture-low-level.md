# Architecture Low-Level — Instruction Template

Craft guidance for writing `docs/architecture/low-level.md`.
Content contract (must-present, keep-out, Diátaxis mode): `references/document-catalog.md`
→ "architecture/low-level.md — component decomposition". Depth: `references/depth-and-audience.md`.

## Purpose
Explain how major subsystems work internally — component decomposition and data flow.

## Data Requirements
- Knowledge graph (required) — module map, layers, import edges
- `/understand-explain <path>` per significant subsystem (required for depth, not optional)

## Template Structure
Per major subsystem:
- One-line purpose, then a 1–2 sentence conceptual overview (the big idea).
- Main components and their responsibilities.
- Call flow for common operations (happy path + key branches).
- Data structures and transformations.
- Error handling and edge cases.
- Integration with the rest of the system.
Use sequence / state / call-tree diagrams for complex flows.

## Provenance Requirements
- Tag each component with its module path from the knowledge graph.
- Reference functions/types by name, never by line number.
- Record git blob hashes of the key modules implementing each subsystem.
- Cross-reference high-level.md for block context and flows/ for runtime choreography.

## Notes
- Aim for a depth where someone could implement a feature without reading the source.
- Don't assume the reader knows every library/framework — explain the unfamiliar ones.
- Link `/understand-explain` output as the evidence behind your assertions.
- Explain *why* the design is this way; the *decision* itself belongs in an ADR — link it.
