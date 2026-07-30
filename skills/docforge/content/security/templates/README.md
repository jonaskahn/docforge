# security templates

Scaffold template files owned by the `security` group.

## Contents

- `api-authentication.md` — Public surface, inputs/outputs, auth contract, limits, errors, compatibility source → [api-authentication.md](api-authentication.md)
- `data-handling.md` — Data classes, lifecycle, access, retention, deletion → [data-handling.md](data-handling.md)
- `economic-invariants.md` — Contracts, storage, authorities, networks, upgrade boundary, economic/security invariants → [economic-invariants.md](economic-invariants.md)
- `platform-permissions.md` — Requested capability, trigger, user value, denial behavior, settings/recovery, manifest evidence → [platform-permissions.md](platform-permissions.md)
- `root-security.md` — Supported scope, reporting path, response expectations, safe harbor → [root-security.md](root-security.md)
- `threat-model.md` — Assets, trust boundaries, threats, controls, accepted residual risk → [threat-model.md](threat-model.md)

## Boundaries

Files here are referenced by exact path from catalog records (`.metadata/catalog/documents/security/`); do not rename without updating the referencing record.
