# Evidence presentation

Provenance establishes that a claim is grounded. Reader-facing content explains
the claim and routes the reader to the owning documentation. These are
separate concerns.

## Policy

- Every substantive heading has a complete provenance entry in the document's
  folder sidecar, including source paths, roles, and blob hashes.
- Never show source paths, line ranges, blob hashes, or source-code links as
  claim citations in generated documentation.
- Show a repository path only when the reader must open, edit, run, or inspect
  that file. It is not evidence and must not be appended to a behavioral claim.
- Use a compact `Related` footer only for generated documentation that already
  exists and owns an adjacent topic. Omit the footer when there is no useful
  destination.

```markdown
> **Related:** [Dead-letter replay](../flows/dlq-replay.md), [Worker recovery](../operations/worker-recovery.md).
```

- `compact` permits a short `Related` footer with relevant generated documents.
- `traceability` permits an evidence or traceability table when the table is
  itself the document's subject, such as a threat register or backlog record.
- `none` omits reader-facing routing while retaining provenance.

An evidence gap is explicit prose, not an empty footer: `Repository evidence
does not establish the retention period.`
