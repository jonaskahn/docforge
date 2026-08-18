# records

Architecture decision records.

## Load this when

- Writing or revising a `records` group document → resolve its contract/instruction/template via `query_catalog --route <document-id>`

## Contents

- `adr.contract.md` — Indexed decisions; for each ADR context, decision, alternatives, consequences, status → [adr.contract.md](adr.contract.md)
- `decision-index.contract.md` — What decision records are, the status lifecycle, and the reader question each record answers → [decision-index.contract.md](decision-index.contract.md)
- `decision-index.template.md` — Scaffold for the decision log README → [decision-index.template.md](decision-index.template.md)

## Boundaries

Owns contracts and templates used exclusively by `records` documents. The ADR instruction and template are shared with portfolio decision documents, so those live in [`../shared/`](../shared/README.md) instead.
