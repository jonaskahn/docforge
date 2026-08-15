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
- [`references/evidence-presentation.md`](references/evidence-presentation.md):
  reader-facing routing and source-evidence visibility.
- [`references/code-presentation.md`](references/code-presentation.md): fenced
  content roles, examples, and source-excerpt boundaries.
- [`references/document-audit.md`](references/document-audit.md): independent
  completion gate.
- [`references/quality-bar.md`](references/quality-bar.md): mechanical and
  whole-tree acceptance.
- [`references/host-neutrality.md`](references/host-neutrality.md): neutral
  vocabulary, forge-confinement.
- [`references/portfolio.md`](references/portfolio.md): cross-repository
  diligence.
- [`references/illustration.md`](references/illustration.md): visual form
  selection and illustration constraints.
- [`references/depth-and-audience.md`](references/depth-and-audience.md):
  reader-facing depth (decision-relevant detail, not file/word count) and
  audience-driven content scope.
- [`references/model-depth-ladders.md`](references/model-depth-ladders.md):
  `model_depth` rigor floors, distinct from reader-facing `target_depth`.
- [`references/parallel-execution.md`](references/parallel-execution.md):
  read-only evidence fan-out and the serial-orchestrator/parallel-worker
  contract.
- [`references/source-analysis.md`](references/source-analysis.md): the
  bounded evidence ladder for querying a selected graph provider.
- [`references/discovery-gate.md`](references/discovery-gate.md):
  open-vocabulary profile-cue judgment after deterministic detection.
- [`references/decision-records.md`](references/decision-records.md): when a
  decision earns a durable record and where it lives.
- [`references/profiles/README.md`](references/profiles/README.md):
  audience and repository-shape reader-facing guidance.
- [`references/docs-tree.md`](references/docs-tree.md): project scale
  classification and compact/standard layout (in addition to paths, naming,
  tiers, and placement above).
- [`workflows/revision.md`](workflows/revision.md): document retirement and
  current-template conformance enforcement.
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
| `workflows/dashboard.md` | `dashboard scan`/`start`/`status`/`stop`: diagnostics, metadata reconcile, signatures, build-if-changed, serve, open |
| `workflows/tools.md` | Every public script: Python/Node invocation, inputs, outputs, exit codes |

See [`workflows/README.md`](workflows/README.md) to route an unfamiliar
invocation to exactly one file.

## Internal Runtime Conventions

- **Dual Field Naming**: Catalog records own `template_file` (specifying the source template path under `content/`), while materialized project manifests carry `scaffold_template` (copied from `template_file` during manifest scaffolding to maintain legacy manifest compatibility).
- **Two Special-File Sets**: The runtime maintains two distinct special-file sets defined in [`runtime/common/python/special_files`](runtime/common/python/special_files.py):
  - `SPECIAL_DOC_SOURCES` (`{"agents-kernel.md", "claude-md.md", "claude-local-md.md"}`): template source filenames scanned during metadata validation (`validate_metadata`).
  - `SPECIAL_DOC_OUTPUTS` (`{"AGENTS.md", "CLAUDE.md", "CLAUDE.local.md"}`): materialized output doc filenames that bypass standard linting and scaffolding constraints (`scaffold_docs`, `lint_document`, `migrate_metadata`). `AGENTS.md` is not unlinted for that: it is covered by the dedicated `lint_agents_kernel` rubric check in place of `lint_document`. The fixed shims (`CLAUDE.md`, `CLAUDE.local.md`) are emitted literally and need no rubric lint.
