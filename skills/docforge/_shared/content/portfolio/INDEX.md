# portfolio

Cross-repository portfolio layer for multi-repo diligence.

## Load this when

- Writing or revising a `portfolio` group document → resolve its contract/instruction/template via `query_catalog --route <document-id>`

## Contents

- [contracts/](contracts/INDEX.md) — 10 contracts
- [templates/](templates/INDEX.md) — 7 templates
- `diligence-index.instruction.md` — Evidence map, gaps, confidence, follow-up → [diligence-index.instruction.md](diligence-index.instruction.md)
- `epic.instruction.md` — Initiative outcome; member repos spanned; per repo, owning flow/feature and component touched; cross-repo sequence tying them together; open gaps → [epic.instruction.md](epic.instruction.md)
- `security-posture.instruction.md` — Cross-repo controls, gaps, shared dependencies, operational coupling → [security-posture.instruction.md](security-posture.instruction.md)
- `system-context.instruction.md` — Repository/system boundaries, shared services, cross-repo flows, directed dependency edges between members with coupling type and resolution confidence → [system-context.instruction.md](system-context.instruction.md)

## Boundaries

Owns contracts, instructions, and templates used exclusively by `portfolio` documents. Artifacts used by more than one group live in [`../shared/`](../shared/INDEX.md) instead.
