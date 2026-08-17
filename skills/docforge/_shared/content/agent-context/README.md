# agent-context

Self-contained coding-agent kernels, topic views, local preferences, and safe
machine settings.

## Load this when

- Writing or revising a `agent-context` group document → resolve its contract/instruction/template via `query_catalog --route <document-id>`

## Contents

- [contracts/](contracts/README.md) — 10 contracts
- [templates/](templates/README.md) — 10 templates
- `agents-kernel.instruction.md` — Permanent self-contained writing and isolation policy → [agents-kernel.instruction.md](agents-kernel.instruction.md)

## Boundaries

Owns contracts, instructions, and templates used exclusively by `agent-context` documents. Artifacts used by more than one group live in [`../shared/`](../shared/README.md) instead.
