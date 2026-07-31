# root

Root-level entrypoints: README, SKILL.md, and package descriptors.

## Load this when

- Writing or revising a `root` group document → resolve its contract/instruction/template via `query_catalog --route <document-id>`

## Contents

- `changelog.contract.md` — Released versions, dates, user-visible changes, compatibility notes → [changelog.contract.md](changelog.contract.md)
- `changelog.template.md` — Released versions, dates, user-visible changes, compatibility notes → [changelog.template.md](changelog.template.md)
- `docs-index.contract.md` — Selected children and one-line purpose → [docs-index.contract.md](docs-index.contract.md)
- `docs-index.template.md` — Selected children and one-line purpose → [docs-index.template.md](docs-index.template.md)
- `root-readme.contract.md` — Purpose, audience, verified quick start, links to setup/architecture/limitations → [root-readme.contract.md](root-readme.contract.md)
- `root-readme.template.md` — Purpose, audience, verified quick start, links to setup/architecture/limitations → [root-readme.template.md](root-readme.template.md)

## Boundaries

Owns contracts, instructions, and templates used exclusively by `root` documents. Artifacts used by more than one group live in [`../shared/`](../shared/INDEX.md) instead.
