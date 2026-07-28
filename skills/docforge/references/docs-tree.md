# Documentation tree

This file owns paths, naming, tiers, and placement. The canonical selectable
path list is `.metadata/catalog.json`.

## Naming and placement

- Reader documentation lives under `docs/`.
- Root files exist only where repository tooling expects them: `README.md`,
  `CHANGELOG.md`, `CONTRIBUTING.md`, `SECURITY.md`, and explicitly selected
  agent shims/configuration.
- Portfolio documents live under `docs-portfolio/`.
- Collection folders use plural nouns; single-subject areas use singular nouns.
- Every selected folder index is a manifest document. Its table is generated
  from selected manifest entries, never from a generic empty list.
- Actual flows, decisions, runbooks, datasets, concepts, migrations, and
  portfolio decisions are dynamically discovered. Do not create example files.
- A flow or concept stays a flat file until real deeper material is written in
  the same operation; see `document-composition.md`.

## Tiers

`spine`, `diligence`, and `portfolio` are the only tier identifiers, in that
order. Higher tiers include lower tiers.

### Spine

Spine supplies the universal front doors and operating baseline:

```text
README.md
CHANGELOG.md
docs/
  README.md
  product/README.md
  product/overview.md
  architecture/README.md
  architecture/high-level.md
  engineering/README.md
  engineering/setup.md
  engineering/testing.md
  reference/README.md
  reference/configuration.md
  reference/limitations.md
```

### Diligence

Diligence adds detailed architecture, discovered flows and decisions, risk and
dependency records, security, operations/runbook indexes, release/contribution
guidance, and a glossary. Conditional conventions documents appear only when a
conventions source exists.

### Portfolio

Portfolio includes all Diligence documents plus:

```text
docs-portfolio/
  README.md
  repo-inventory.md
  system-context.md
  decisions/README.md
  security-posture.md
  operations.md
  diligence-index.md
  glossary.md
```

Actual cross-repository decisions are dynamic entries under
`docs-portfolio/decisions/`.

## Overlays

Overlay identifiers and order come from the catalog. Shared paths are defined
once with multiple overlay selectors, so selection retains every origin without
duplicating the document.

Audience overlay roots are intentionally visible in the plan:

```text
docs/product/business-analyst/
  README.md
  process-flows.md
  business-rules.md
  requirements-traceability.md

docs/product/product-owner/
  README.md
  feature-catalog.md
  success-metrics.md
  release-notes.md
  backlog-traceability.md  # dynamic; only with ticket evidence

AGENTS.md
CLAUDE.md
CLAUDE.local.md
.claude/settings.json
docs/agents/
  README.md
  architecture.md
  patterns.md
  testing.md
  tech-debt.md
  conventions.md  # conditional on an existing conventions source
  flow.md
  glossary.md
```

Only the BA process/rule/traceability set and the agent flow/flow-derived
glossary views require a flow graph. Product Owner documents use code,
manifests, history, ticket evidence, and stakeholder evidence as applicable;
they do not globally hard-gate on flow data.

## Existing documentation

Before moving existing documents, inventory and propose one action per file:
keep, migrate, merge, archive, or delete. Moving, merging, archiving, and
deleting require explicit user approval. Archive approved obsolete material
under `docs/_archive/<year>/`; audits exclude that directory.
