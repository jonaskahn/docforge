# Independent document audit

This file owns the completion gate.

## Independence

Start a separate cold artifact-only pass after writing. Review only:

- the finished artifact;
- its catalog content contract and audit profile;
- target depth;
- its group's voice ([`voice.md`](voice.md)) — checked the same way depth and
  mode are checked, never as a heading checklist;
- its level discipline
  ([`progressive-disclosure.md`](progressive-disclosure.md)) — checked the same
  way voice is: does the document state its outcome before its mechanism, is
  every item named before any item is explained, and does an L1 section carry
  L2 detail for one item only;
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

The contract in force is the stable route returned by
`query_catalog.{py,js} --route`. Every agent-context artifact must stand
alone; any Markdown link, URL, `@` import, peer-agent or human-document
reference, or bare generated-document path is a `FAIL`. Plain
source/configuration paths and verified commands are allowed. A generated
non-agent artifact that mentions or references any agent-context output is
also a `FAIL`. The whole-tree audit reports those directions as
`agent-context outbound` and `agent-context leak`, respectively.

Record the result with `manage_manifest.{py,js} audit` (see
[`../runtime/manifest/README.md`](../runtime/manifest/README.md)). A failure
puts the document in `needs_review`. `manage_manifest.{py,js} set --status
complete` rejects a document without a passing `cold-pass` audit record.
Mechanical lint alone cannot produce PASS.

Root-kernel outputs (`AGENTS.md` and `CLAUDE.md`, both
`SPECIAL_DOC_OUTPUTS` members that `lint_document.{py,js}` skips) are linted
by `lint_agents_kernel.{py,js}` instead (see
[`../runtime/documents/README.md`](../runtime/documents/README.md)); its
defects are mechanical failures that block `PASS`. The local-preference
extension is emitted literally and carries no kernel rubric.
