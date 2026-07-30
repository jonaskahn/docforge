# agent-context

Agent-facing context: AGENTS.md and coding-agent views.

## Load this when

- Writing or revising a `agent-context` group document → resolve its contract/instruction/template via `query_catalog --route <document-id>`

## Contents

- [contracts/](contracts/README.md) — 10 contracts
- [templates/](templates/README.md) — 11 templates
- `agents-kernel.instruction.md` — Compact entry points, verified commands, precedence, safe links to owning agent views → [agents-kernel.instruction.md](agents-kernel.instruction.md)

## Boundaries

Owns contracts, instructions, and templates used exclusively by `agent-context` documents. Artifacts used by more than one group live in [`../shared/`](../shared/README.md) instead.
