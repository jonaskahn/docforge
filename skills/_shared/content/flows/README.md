# flows

End-to-end flow documentation derived from the flow index.

## Load this when

- Writing or revising a `flows` group document → resolve its contract/instruction/template via `query_catalog --route <document-id>`

## Contents

- `flow-index.contract.md` — Every evidence-backed candidate, normalized entry reference, area, confidence, reach, priority, and main/deferred/placeholder/documented/skipped status → [flow-index.contract.md](flow-index.contract.md)
- `flow-index.template.md` — Every evidence-backed candidate, normalized entry reference, area, confidence, reach, priority, and main/deferred/placeholder/documented/skipped status → [flow-index.template.md](flow-index.template.md)
- `flow.contract.md` — Trigger, actors, ordered steps, branches, rules, failures, outcome → [flow.contract.md](flow.contract.md)
- `flows.instruction.md` — Trigger, actors, ordered steps, branches, rules, failures, outcome → [flows.instruction.md](flows.instruction.md)

## Boundaries

Owns contracts, instructions, and templates used exclusively by `flows` documents. Artifacts used by more than one group live in [`../shared/`](../shared/README.md) instead.
