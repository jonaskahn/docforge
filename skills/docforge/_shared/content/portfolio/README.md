# portfolio

Cross-repository portfolio layer for multi-repo diligence.

## Load this when

- Writing or revising a `portfolio` group document → resolve its contract/instruction/template via `query_catalog --route <document-id>`

## Contents

- [contracts/](contracts/README.md) — 10 contracts
- [templates/](templates/README.md) — 7 templates
- `instructions.md` — Merged writing craft, one section per document (diligence-index, epic, repo-inventory, security-posture/portfolio-operations, system-context) → [instructions.md](instructions.md)

## Boundaries

Owns contracts, instructions, and templates used exclusively by `portfolio` documents. Artifacts used by more than one group live in [`../shared/`](../shared/README.md) instead.
