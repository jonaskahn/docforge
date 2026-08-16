# `operations_compact`

Content contract for compact document type `operations_compact`.

The merged `docs/operations.md` is the compact form of the operations
section: the section-level orientation (deployment, observability, and
operational boundaries) followed by deployment and observability, one `##`
section per member below. Runbooks stay a separate, dynamically discovered
index (`docs/operations/runbooks/README.md`) — this file links to it rather
than folding it, since runbook instances have no fixed count to merge.
Each section follows its member's own content contract; the composed
contract for this document lists the members this project's manifest
actually selected.

| Type | Must present | Keep out | Primary mode | Depth |
|---|---|---|---|---|
| operations_compact | section introduction, at-a-glance operational shape, scope and boundaries, deployment (environments, artifact path, rollout, rollback, verification), observability (signals, ownership, correlation, alert intent, blind spots); links to every selected, materialized document in this section's folder that this file does not merge | incident procedures, provider marketing, runbook content (owned by the runbooks index), direct source-file navigation | Explanation | orientation |
