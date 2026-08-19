# architecture

System architecture: structure, boundaries, and integration surfaces.

## Load this when

- Writing or revising a `architecture` group document → resolve its contract/instruction/template via `query_catalog --route <document-id>`

## Contents

- [contracts/](contracts/README.md) — 28 contracts
- [instructions.md](instructions.md) — merged writing craft for 26 document types, one section per document; `contract_system` and `host_integration` route to shared instructions instead (each pairs with a document in another group)
- [templates/](templates/README.md) — 27 templates

## Boundaries

Owns contracts, instructions, and templates used exclusively by `architecture` documents. Artifacts used by more than one group live in [`../shared/`](../shared/README.md) instead.
