# architecture

System architecture: structure, boundaries, and integration surfaces.

## Load this when

- Writing or revising a `architecture` group document → resolve its contract/instruction/template via `query_catalog --route <document-id>`

## Contents

- [contracts/](contracts/README.md) — 28 contracts
- [instructions/](instructions/README.md) — 26 instructions
- [templates/](templates/README.md) — 27 templates

## Boundaries

Owns contracts, instructions, and templates used exclusively by `architecture` documents. Artifacts used by more than one group live in [`../shared/`](../shared/README.md) instead.
