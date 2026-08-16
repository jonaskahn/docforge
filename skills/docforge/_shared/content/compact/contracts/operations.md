# `operations_compact`

Content contract for compact document type `operations_compact`.

The merged `docs/operations.md` is the compact form of the operations
section: the section-level orientation (deployment, observability, and
operational boundaries) followed by deployment and observability, one `##`
section per member below. It also carries the runbook register and one `##`
section per folded runbook; every discovered runbook keeps a register row
whether or not it earned a section. Each section follows its member's own
content contract; the composed contract for this document lists the members
this project's manifest actually selected.

| Type | Must present | Keep out | Primary mode | Depth |
|---|---|---|---|---|
| operations_compact | section introduction, at-a-glance operational shape, scope and boundaries, deployment (environments, artifact path, rollout, rollback, verification), observability (signals, ownership, correlation, alert intent, blind spots), the runbook register, one section per folded runbook carrying trigger, verified steps, and recovery outcome; links to every selected, materialized document in this section's folder that this file does not merge | provider marketing, a register-only runbook written up as though its procedure had been verified, direct source-file navigation | Explanation | orientation |
