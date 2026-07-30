# records

Architecture decision records.

## Load this when

- Writing or revising a `records` group document → resolve its contract/instruction/template via `query_catalog --route <document-id>`

## Contents

- `adr.contract.md` — Indexed decisions; for each ADR context, decision, alternatives, consequences, status → [adr.contract.md](adr.contract.md)
- `decision-index.contract.md` — Indexed decisions; for each ADR context, decision, alternatives, consequences, status → [decision-index.contract.md](decision-index.contract.md)

## Boundaries

Owns contracts, instructions, and templates used exclusively by `records` documents. Artifacts used by more than one group live in [`../shared/`](../shared/README.md) instead.
