# Independent document audit

This file owns the completion gate.

## Independence

Start a separate cold artifact-only pass after writing. Review only:

- the finished artifact;
- its catalog content contract and audit profile;
- target depth;
- applicable quality checks;
- sources cited by validated current provenance, after the mechanical gate has
  confirmed concrete metadata, source blobs, and heading-matched sections;
- for a template rewrite or revision only, the document's prior committed
  version, solely to check illustration continuity (see Verdict).

Do not include writer reasoning or draft conversation. Record
`mode: cold-pass`.

## Verdict

The audit report records document id/path, mode, verdict, evidence checked,
defects, and disposition, shaped by
[`audit-report.md`](../content/shared/audit-report.template.md).

- `PASS`: every must-present element is supported, the keep-out boundary holds,
  depth and mode fit, and mechanical checks pass.
- `FAIL`: at least one derivable gap, unsupported claim, structural defect, or
  unresolved non-external placeholder remains — including a template rewrite
  or revision that dropped an illustration relative to its prior committed
  version without its facts surviving in prose or table form elsewhere in the
  document, and without those facts being genuinely superseded or incorrect.

Atomic external values may remain as typed `<UPPER_SNAKE_CASE>` tokens. A
derivable gap may not be waived to a human.

The contract in force is the one `query_catalog.{py,js} --route` returned for
this run's agent-context mode. In `standalone` mode an agent-context document
legitimately owns facts the `linked` contract lists under Keep out; owning them
is not a `FAIL`. A standalone document that instead links a human-facing
document this run never generated **is** a `FAIL` — both a dead link and a fact
with no owner. Symmetrically, a human-facing document that references any
agent-context path is a `FAIL` in either mode (the `agent-context leak` finding
in `scaffold_docs --audit`).

Record the result with `manage_manifest.{py,js} audit` (see
[`../runtime/manifest/README.md`](../runtime/manifest/README.md)). A failure
puts the document in
`needs_review`. `manage_manifest.{py,js} set --status complete` rejects a
document
without a passing `cold-pass` audit record. Mechanical lint alone
cannot produce PASS.

AGENTS.md-shaped outputs (`AGENTS.md`, a `SPECIAL_DOC_OUTPUTS` member that
`lint_document.{py,js}` skips) are linted by `lint_agents_kernel.{py,js}`
instead (see [`../runtime/documents/README.md`](../runtime/documents/README.md));
its defects
are mechanical failures that block `PASS`. Fixed shims are emitted literally
and carry no rubric lint.
