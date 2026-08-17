# security

Security posture, permissions, and threat model.

## Load this when

- Writing or revising a `security` group document → resolve its contract/instruction/template via `query_catalog --route <document-id>`

## Contents

- [contracts/](contracts/README.md) — 6 contracts
- [templates/](templates/README.md) — 6 templates
- `instructions.md` — Merged writing craft for `api-authentication`, `data-handling`, `platform-permissions`, `security-policy` (`security_root`), `threat-model`, `threat-register`; one section per document → [instructions.md](instructions.md)

## Boundaries

Owns contracts, instructions, and templates used exclusively by `security` documents. Artifacts used by more than one group live in [`../shared/`](../shared/README.md) instead.
