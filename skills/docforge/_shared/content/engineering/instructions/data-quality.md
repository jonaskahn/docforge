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
scheduled audit). Distinguish a check that blocks bad data from one
that only observes and alerts on it.

State what happens when a check fails: reject, quarantine, alert-only, or
auto-correct. Where a quality guarantee is evidenced only by a sample or a
subset, say so plainly rather than letting a scoped guarantee read as
universal.
