# Canonical ownership

- [`references/docs-tree.md`](references/docs-tree.md): paths, naming, tiers,
  placement.
- [`content/README.md`](content/README.md): must-present content, keep-out
  boundaries, mode, and depth — one contract per document type, routed by
  group.
- [`references/graph/`](references/graph/README.md): provider dispatch and
  selection.
- [`references/document-composition.md`](references/document-composition.md):
  topic ownership and no-duplication.
- [`references/provenance-tracking.md`](references/provenance-tracking.md):
  metadata format and staleness.
- [`references/document-audit.md`](references/document-audit.md): independent
  completion gate.
- [`references/quality-bar.md`](references/quality-bar.md): mechanical and
  whole-tree acceptance.
- [`references/host-neutrality.md`](references/host-neutrality.md): neutral
  vocabulary, forge-confinement.
- [`references/portfolio.md`](references/portfolio.md): cross-repository
  diligence.
- `content/<group>/instructions/`: document-specific writing craft only.
- `content/<group>/templates/`: output scaffolds only.

When a rule changes, update its owner and replace other repetitions with a
link.

## Workflow files

| File | Owns |
|---|---|
| `workflows/intake.md` | Bare `/docforge` invocation, discovery gate, scope questions, confirmation, graph-provider choice |
| `workflows/planning.md` | Repository inspection, tier/profile selection, dynamic-document discovery, manifest init, dry-run tree, plan checkpoint |
| `workflows/writing.md` | Per-document execution card, evidence, scaffolding, provenance, status transitions, independent audit; continue incomplete runs |
| `workflows/revision.md` | `/docforge-revise` (incl. shared flags), single-document update/refresh, flow-index organization |
| `workflows/validation.md` | Staleness, migration, whole-tree audit, cross-document quality gate |
| `workflows/tools.md` | Every public script: Python/Node invocation, inputs, outputs, exit codes |

See [`workflows/README.md`](workflows/README.md) to route an unfamiliar
invocation to exactly one file.
