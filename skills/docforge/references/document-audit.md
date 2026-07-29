# Independent document audit

This file owns the completion gate.

## Independence

Prefer a fresh artifact-only subagent that did not write the document. Give it
only:

- the finished artifact;
- its catalog content contract and audit profile;
- target depth;
- applicable quality checks;
- sources cited by validated provenance 2.0, after the mechanical gate has
  confirmed concrete metadata, source blobs, and heading-matched sections.

Do not include writer reasoning or draft conversation. If fresh subagents are
unavailable, start a separate cold artifact-only pass and record
`mode: cold-pass`.

## Verdict

The audit report records document id/path, mode, verdict, evidence checked,
defects, and disposition.

- `PASS`: every must-present element is supported, the keep-out boundary holds,
  depth and mode fit, and mechanical checks pass.
- `FAIL`: at least one derivable gap, unsupported claim, structural defect, or
  unresolved non-external placeholder remains.

Atomic external values may remain as typed `<UPPER_SNAKE_CASE>` tokens. A
derivable gap may not be waived to a human.

Record the result with `manage_manifest audit`. A failure puts the document in
`needs_review`. `manage_manifest set --status complete` rejects a document
without a passing `subagent` or `cold-pass` audit record. Mechanical lint alone
cannot produce PASS.
