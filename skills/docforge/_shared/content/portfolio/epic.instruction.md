# Epic (portfolio) writing craft

Ground each repository contribution and handoff in member documentation or history
evidence. Mark an unproved sequence as an open gap; assign an owner token only
when evidenced, otherwise use `undetermined` and link the follow-up in
`diligence-index`.

An epic names a cross-repository initiative. State the outcome first, then the
member repos it spans with each repo's owning flow/feature and component, then
the cross-repo sequence that ties them together. Link to member documents by
path; do not restate member-internal call graphs or invent scope.

Open gaps stay explicit — missing owners, unresolved handoffs, or undetermined
sequencing. Epics are added
manually via `manage_manifest add --type epic` (agent-asserted
`discovered_epic`), mirroring portfolio decisions.

## Illustration

- **Form:** a `sequenceDiagram` that spans the member repos in initiative
  order.
- **Renders:** each member repo as a participant and each cross-repo handoff
  as a labeled call, in the order the initiative actually proceeds.
- **Trigger:** always for this document type — the cross-repo sequence is the
  point — within
  [`../../references/illustration.md`](../../references/illustration.md)'s
  5-participant limit.

## Connections

| This document owns | Links to | Because |
|---|---|---|
| Outcome, member repos, owning flow/feature/component per repo, cross-repo sequence | each member repo's own `flow` document | the member's internal steps are owned there; this document only names which flow/feature each repo contributes |
| — | `system-context` | system-context maps portfolio-wide boundaries; this document maps one initiative's path across them |
| An unresolved handoff or missing owner | `diligence-index` | an open gap in the initiative is exactly the kind of claim diligence-index exists to track |
