# Epic (portfolio) writing craft

**Preferred illustration:** Follow
[`../../references/illustration.md`](../../references/illustration.md); a
`sequenceDiagram` that spans the member repos in initiative order.

An epic names a cross-repository initiative. State the outcome first, then the
member repos it spans with each repo's owning flow/feature and component, then
the cross-repo sequence that ties them together. Link to member documents by
path; do not restate member-internal call graphs or invent scope.

Open gaps stay explicit — missing owners, unresolved handoffs, or undetermined
sequencing — so a reviewer can see what still needs evidence. Epics are added
manually via `manage_manifest add --type epic` (agent-asserted
`discovered_epic`), mirroring portfolio decisions.
