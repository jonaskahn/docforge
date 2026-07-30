# security

Security posture, permissions, and threat model.

## Load this when

- Writing or revising a `security` group document → resolve its contract/instruction/template via `query_catalog --route <document-id>`

## Contents

- [contracts/](contracts/README.md) — 6 contracts
- [templates/](templates/README.md) — 6 templates
- `api-authentication.instruction.md` — Public surface, inputs/outputs, auth contract, limits, errors, compatibility source → [api-authentication.instruction.md](api-authentication.instruction.md)
- `data-handling.instruction.md` — Data classes, lifecycle, access, retention, deletion → [data-handling.instruction.md](data-handling.instruction.md)
- `platform-permissions.instruction.md` — Requested capability, trigger, user value, denial behavior, settings/recovery, manifest evidence → [platform-permissions.instruction.md](platform-permissions.instruction.md)
- `security-policy.instruction.md` — Supported scope, reporting path, response expectations, safe harbor → [security-policy.instruction.md](security-policy.instruction.md)
- `threat-model.instruction.md` — Assets, trust boundaries, threats, controls, accepted residual risk → [threat-model.instruction.md](threat-model.instruction.md)

## Boundaries

Owns contracts, instructions, and templates used exclusively by `security` documents. Artifacts used by more than one group live in [`../shared/`](../shared/README.md) instead.
