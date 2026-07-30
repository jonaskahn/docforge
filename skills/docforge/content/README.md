# Content

Contracts, instructions, and templates for every catalog document, organized by group. This directory owns must-present material, keep-out boundaries, primary mode, target depth, and writing craft; selection, paths, evidence capabilities, write order, and audit profiles are machine-readable via `query_catalog` against `.metadata/catalog/`.

## Load this when

- Writing or revising a document → resolve its contract/instruction/template in one call via `query_catalog --route <document-id>`.
- Choosing among documents in a group before an id is known → `query_catalog --category <group>`.

## Contents

- [agent-context/](agent-context/README.md) — Agent-facing context: AGENTS.md and coding-agent views.
- [architecture/](architecture/README.md) — System architecture: structure, boundaries, and integration surfaces.
- [contributing/](contributing/README.md) — Contribution guidelines and root-level contributor docs.
- [engineering/](engineering/README.md) — Engineering practices: conventions, testing, and tech debt.
- [flows/](flows/README.md) — End-to-end flow documentation derived from the flow index.
- [operations/](operations/README.md) — Deployment, observability, and operational runbooks.
- [portfolio/](portfolio/README.md) — Cross-repository portfolio layer for multi-repo diligence.
- [product/](product/README.md) — Product surface: overview, quickstart, and audience-specific product views.
- [records/](records/README.md) — Architecture decision records.
- [reference/](reference/README.md) — Reference lookups: APIs, configuration, and glossary.
- [root/](root/README.md) — Root-level entrypoints: README, SKILL.md, and package descriptors.
- [security/](security/README.md) — Security posture, permissions, and threat model.
- [shared/](shared/README.md) — artifacts referenced by more than one group

## Universal contract

Every substantive document must:

- answer the reader question implied by its type;
- cite the repository evidence used by each section;
- describe current behavior, boundaries, failure modes, and adjacent systems;
- keep rationale in decision records and volatile lookup facts in reference
  documents;
- link to facts owned elsewhere instead of repeating them;
- contain no unresolved scaffold markers.

Router/index documents orient and link. Procedure documents are executable in
order. Reference documents optimize lookup. Explanation documents establish
mechanism, constraints, and tradeoffs.

## Risk-register routing

Route each bound by who can change it and whether it is user-visible: fixable by
us later → `tech-debt-register`; imposed from outside and immovable →
`constraints`; deliberate or accepted and user-visible → `limitations-register`.
Never cross-file them. For `threat-model`, keep the analysis proportionate; the
accepted-risk section is the reviewer's signal that analysis was performed.
When more rigor is warranted, use a trust-boundary data-flow with STRIDE per
element and one response per threat (mitigate / eliminate / transfer / accept)
tied to a testable control — link `data-handling` classifications; do not
restate the inventory.

## Typed profile behavior

- Shapes own document packs. API and library references derive their public surface from specs, schemas, or
  exported interfaces; do not hand-maintain a parallel API.
- Platforms own runtime compatibility, permissions, lifecycle, packaging,
  signing, and distribution details inside the shared client documents.
- Framework profiles change detection, graph queries, terminology, and verified
  commands only. They do not create `flutter-*`, `electron-*`, or equivalent
  duplicate document families.
- Concerns add a document only when the catalog explicitly owns one; otherwise
  they add a section to the existing topic owner.
- Data contracts name producers, consumers, schema, validation, lineage,
  compatibility, and recovery.
- Business Analyst documents own a business-language process view, rules, and
  requirements traceability. The process view links each item to its canonical
  dynamic flow document; it does not duplicate technical call-chain prose.
- Product Owner documents own feature value/status, evidenced measures, and
  user-facing release notes. Backlog traceability is dynamic and exists only
  with ticket evidence.
- Agent views are compact linking views. Architecture and patterns require the
  code graph; only flow and flow-derived glossary views require the flow graph;
  conventions require a conventions source.

The optional instruction file named by the catalog adds writing craft only. It
must not redefine this contract.

## Boundaries

Every content-contract, instruction, and template file referenced by `.metadata/catalog/` lives under this tree. No group duplicates a shared artifact; no artifact lives outside its owning group or `shared/`.
