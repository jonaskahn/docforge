# Data-quality writing craft

For each governed dataset, identify producer, transformation boundary, linked
data contract, schema owner, and recovery or runbook handoff. Ground checks in
their implementation; use a bounded ER diagram only for evidenced durable
relationships, never inferred lineage or cardinality.

**Preferred illustration:** Follow
[`../../../references/illustration.md`](../../../references/illustration.md); a table
mapping dimension to check and enforcement point.

Organize by quality dimension — accuracy, completeness, timeliness,
validity, uniqueness, consistency — and for each, state what is actually
checked and where the check runs (ingestion, transformation, or a
scheduled audit); a claimed dimension with no enforcement point is
aspiration, not quality. Distinguish a check that blocks bad data from one
that only observes and alerts on it — a reader deciding whether to trust a
dataset needs to know which kind protects them.

State what happens when a check fails: reject, quarantine, alert-only, or
auto-correct — never leave failure behavior implicit. Where a quality
guarantee is evidenced only by a sample or a subset, say so plainly rather
than letting a scoped guarantee read as universal; an unevidenced lineage
or sample-only claim presented as a full guarantee is the failure mode this
document exists to prevent.
