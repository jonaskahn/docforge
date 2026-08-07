---
docforge_provenance:
  schema: "2.1"
  doc_id: "<DOC_ID>"
  path: "<DOCUMENT_PATH>"
  generated_at: "<GENERATED_AT>"
  generator:
    name: "docforge"
    version: "2.8.0"
  tier: "<TIER>"
  target_depth: "<TARGET_DEPTH>"
  graph:
    provider: "<GRAPH_PROVIDER>"
    flow: "<FLOW_CAPABILITY>"
  sections: []
---
<!-- Prune every row below that points at a document this repo does not have.
     A router with dead links is worse than a short one. -->

# Documentation

{{Two or three sentences that introduce the documentation itself: what this
repository is, who the documentation is for, and how it is organized.}}

## At a glance

{{One or two sentences describing the overall documentation shape: product
understanding, architecture, engineering practice, operations, reference, and
security each live in their own section; audience-specific views exist for
Business Analysts, Product Owners, and coding agents when selected.}}

## Start here

| You are | Read |
|---|---|
| New to the project | [product/overview.md](product/overview.md) |
| A new engineer | [architecture/high-level.md](architecture/high-level.md) → [engineering/setup.md](engineering/setup.md) |
| Consuming this service | [product/quickstart.md](product/quickstart.md) → [reference/](reference/README.md) |
| On call | [operations/](operations/README.md) |
| Reviewing risk | [security/](security/README.md) · [architecture/dependencies.md](architecture/dependencies.md) · [reference/limitations.md](reference/limitations.md) |
| Contributing | [contributing/](contributing/README.md) |

## Sections

<!-- docforge-children:start -->
| Folder | Answers |
|---|---|
| {{section link}} | {{the reader question this section answers}} |
<!-- docforge-children:end -->

## Conventions

- Volatile documents carry a `_Last reviewed: YYYY-MM-DD_` line.
- Reference material is generated where a machine-readable source exists; generated
  files say so and name the regeneration command.
- Documentation is host-neutral: forge-specific detail lives only in
  [contributing/README.md](contributing/README.md).
