# shared

Contracts, instructions, and templates referenced across document groups or by the references layer. A shared artifact is never duplicated into a group folder.

## Contents

- `adr.template.md` → [adr.template.md](adr.template.md)
- `audience-deepdive.template.md` → [audience-deepdive.template.md](audience-deepdive.template.md)
- `audit-report.template.md` → [audit-report.template.md](audit-report.template.md)
- `contract-system.instruction.md` → [contract-system.instruction.md](contract-system.instruction.md)
- `decision-records.instruction.md` → [decision-records.instruction.md](decision-records.instruction.md)
- `folder-index.contract.md` → [folder-index.contract.md](folder-index.contract.md)
- `folder-index.instruction.md` → [folder-index.instruction.md](folder-index.instruction.md)
- `generic.template.md` → [generic.template.md](generic.template.md)
- `glossary.instruction.md` → [glossary.instruction.md](glossary.instruction.md)
- `host-integration.instruction.md` → [host-integration.instruction.md](host-integration.instruction.md)
- `section-readme.template.md` → [section-readme.template.md](section-readme.template.md)
- `topic-readme.template.md` → [topic-readme.template.md](topic-readme.template.md)
- `exemplars/` → worked craft references, one fictional service across all four:
  [flow.standard.example.md](exemplars/flow.standard.example.md),
  [flow.compact.example.md](exemplars/flow.compact.example.md),
  [architecture.standard.example.md](exemplars/architecture.standard.example.md),
  [architecture.compact.example.md](exemplars/architecture.compact.example.md)

## Exemplars

The files under `exemplars/` show what the flow and architecture templates
produce when filled well, in both layouts. They are craft references, never
generated artifacts and never templates — no catalog record points at them, and
`query_catalog --route` never returns one.

**Update an exemplar in the same change as the template it demonstrates.** An
exemplar that has drifted from its template teaches the wrong shape, and nothing
mechanical will catch it.

Each one lints clean under `lint_document` except for `missing provenance`,
which is inherent: an exemplar has no folder sidecar because it is not a
document in a docs tree. Every other defect class applies and must stay clean —
that is what proves the shape being taught is a shape the gate accepts.

## Boundaries

An artifact belongs here when it is referenced by more than one group's catalog records, or by the references layer (the promotion and audit procedures) rather than a single group. Group-exclusive artifacts live under `../<group>/` instead.
