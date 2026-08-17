# flows

End-to-end flow documentation derived from the flow index.

## Load this when

- Writing or revising a `flows` group document → resolve its contract/instruction/template via `query_catalog --route <document-id>`

## Contents

- `flow-index.contract.md` — Every evidence-backed candidate, normalized entry reference, area, confidence, reach, priority, and main/deferred/placeholder/documented/skipped status → [flow-index.contract.md](flow-index.contract.md)
- `flow-index.template.md` — Every evidence-backed candidate, normalized entry reference, area, confidence, reach, priority, and main/deferred/placeholder/documented/skipped status → [flow-index.template.md](flow-index.template.md)
- `flow.contract.md` — Trigger, actors, ordered steps, branches, rules, failures, outcome → [flow.contract.md](flow.contract.md)
- `flow.template.md` — Trigger, actors, ordered steps, branches, rules, failures, outcome → [flow.template.md](flow.template.md)
- `instructions.md` — Merged writing craft for `flows_index` and `flow`; one section per document → [instructions.md](instructions.md)

## Boundaries

Owns contracts, instructions, and templates used exclusively by `flows` documents. Artifacts used by more than one group live in [`../shared/`](../shared/README.md) instead.
