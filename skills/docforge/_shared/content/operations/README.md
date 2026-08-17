# operations

Deployment, observability, and operational runbooks.

## Load this when

- Writing or revising a `operations` group document → resolve its contract/instruction/template via `query_catalog --route <document-id>`

## Contents

- [contracts/](contracts/README.md) — 10 contracts
- `instructions.md` — Merged writing craft, one section per document (application-distribution, deployment, disaster-recovery, flashing-recovery, infrastructure-apply/state, job-reliability, network-deployment, observability, runbook) → [instructions.md](instructions.md)
- [templates/](templates/README.md) — 10 templates

## Boundaries

Owns contracts, instructions, and templates used exclusively by `operations` documents. Artifacts used by more than one group live in [`../shared/`](../shared/README.md) instead.
