# Documentation tree

This file owns paths, naming, tiers, and placement. The canonical selectable
path list is `.metadata/catalog/` (queried via `runtime/cli/python/query_catalog.py`).

## Naming and placement

- Reader documentation lives under `docs/`.
- Root files exist only where repository tooling expects them: `README.md`,
  `CHANGELOG.md`, `CONTRIBUTING.md`, `SECURITY.md`, and explicitly selected
  agent shims/configuration.
- Portfolio documents live under `docs-portfolio/`.
- Collection folders use plural nouns; single-subject areas use singular nouns.
- Every selected folder index is a manifest document. Its child map is generated
  from selected manifest entries; the section overview around it (introduction,
  scope, reading paths) is authored from repository evidence. A section README
  is finalized after its child documents, so it links only materialized
  documents.
- Actual flows, decisions, runbooks, datasets, concepts, migrations,
  portfolio decisions, and epics are dynamically discovered. Do not create
  example files.
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
  flows/README.md
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

`docs/flows/README.md` exists at Spine as the rendered complete candidate
matrix backed by `.docforge/flow-index.json`. Revise flow creates stub
`docs/flows/{slug}.md` files for every harvested candidate. Diligence adds
full deep-dive flow documents only for main-priority rows; deferred-priority
stubs remain discoverable in the matrix until promoted.

### Portfolio

Portfolio includes all Diligence documents plus:

```text
docs-portfolio/
  README.md
  repo-inventory.md
  system-context.md
  decisions/README.md
  epics/README.md
  security-posture.md
  operations.md
  diligence-index.md
  glossary.md
```

Actual cross-repository decisions and epics are dynamic entries under
`docs-portfolio/decisions/` and `docs-portfolio/epics/`; both collection
indexes are catalog records (`portfolio_decisions_index`,
`epics_index`). Collection procedure and cross-repository writing
specifics live in [`portfolio.md`](portfolio.md).

## Typed profiles

The catalog owns five independent dimensions:

- **shapes** describe what the repository delivers and select durable document
  packs;
- **platforms** describe where artifacts run and add platform constraints;
- **frameworks** supply detection, terminology, evidence queries, and verified
  commands but do not add a parallel framework tree;
- **concerns** add evidenced cross-cutting documents or sections;
- **audiences** add reader-specific views.

All dimensions are multi-select. Shared paths are defined once with multiple
selectors, retain every matching origin, and never duplicate. Selecting any
child also selects each cataloged ancestor `README.md`; there are no manual
folder-index trigger lists.

### Shape-owned paths

The catalog is authoritative; these families explain placement:

```text
website / web-app
  docs/product/content-model.md
  docs/architecture/{rendering,state,ui-components}.md
  docs/engineering/styling.md
  docs/reference/browser-support.md

mobile-app / desktop-app
  docs/architecture/{application-lifecycle,ui-and-state,platform-integration}.md
  docs/security/permissions.md
  docs/reference/platform-compatibility.md
  docs/operations/distribution.md

worker-serverless
  docs/architecture/triggers-and-jobs.md
  docs/operations/job-reliability.md

cli-tui
  docs/reference/{commands,output-and-exit-codes}.md
  docs/operations/distribution.md

plugin-extension
  docs/architecture/host-integration.md
  docs/reference/extension-points.md
  docs/operations/distribution.md

ml-system
  docs/architecture/model-lifecycle.md
  docs/reference/model-card.md

game
  docs/architecture/{gameplay-systems,assets-and-scenes}.md
  docs/reference/{performance-budgets,platform-compatibility}.md
  docs/operations/distribution.md

embedded-iot
  docs/architecture/{hardware-map,firmware-lifecycle}.md
  docs/reference/performance-budgets.md
  docs/operations/flashing-and-recovery.md

smart-contract
  docs/architecture/contract-system.md
  docs/security/economic-invariants.md
  docs/operations/network-deployment.md
```

API/service, library/SDK, data-pipeline, and infrastructure-platform paths are
the existing canonical packs under product, architecture, engineering,
operations, reference, and security. Platform-specific packaging, signing,
permissions, lifecycle, compatibility, and distribution details are sections
inside their owning documents rather than one file per framework. Additional catalog
layout groups (`worker-serverless`, `plugin-extension`, `ml-system`) define path structure
without separate profile guides.

Detailed composition notes are available for 11 repository shapes:
[API-service](profiles/shape-api-service.md), [web-app](profiles/shape-web-app.md),
[library/SDK](profiles/shape-library-sdk.md), [data-pipeline](profiles/shape-data-pipeline.md),
[infrastructure-platform](profiles/shape-infrastructure-platform.md),
[mobile-app](profiles/shape-mobile-app.md), [desktop-app](profiles/shape-desktop-app.md),
[cli-tui](profiles/shape-cli-tui.md), [game](profiles/shape-game.md),
[embedded-iot](profiles/shape-embedded-iot.md), and [smart-contract](profiles/shape-smart-contract.md).

Audience-profile roots are intentionally visible in the plan:

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

Audience-specific composition notes live in
[Business Analysts](profiles/audience-business-analysts.md),
[Product Owners](profiles/audience-product-owners.md),
[coding agents](profiles/audience-coding-agents.md),
[operators](profiles/audience-operators.md), and
[security reviewers](profiles/audience-security-reviewers.md).

## Existing documentation

Before moving existing documents, inventory and propose one action per file:
keep, migrate, merge, archive, or delete. Moving, merging, archiving, and
deleting require explicit user approval. Archive approved obsolete material
under `docs/_archive/<year>/`; audits exclude that directory.

**Root `README.md` special case.** Catalog `root_readme` targets the
repo-root `README.md`. When that file already exists and is non-trivial /
valuable (substantial user-facing content, not an empty stub), do not silently
overwrite it with the Docforge template. Present exactly **migrate** / **skip**
/ **rewrite** and wait for confirmation before any write:

- **migrate** — reshape into the `root_readme` contract/template; preserve
  purpose, audience, install/quickstart, and other key facts;
- **skip** — leave the file untouched; mark `root_readme` skipped for this run;
- **rewrite** — replace with the Docforge `root_readme` template from fresh
  evidence.

`--auto-accept` does not waive this choice. Stub or placeholder READMEs may
default to rewrite after stating that assessment. Detail:
[`../workflows/planning.md`](../workflows/planning.md).
