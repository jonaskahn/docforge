# Triggers-and-jobs writing craft

**Preferred illustration:** Follow
[`../../../references/illustration.md`](../../../references/illustration.md); a table
per job is primary — trigger, payload, schedule, ownership — prose only
for downstream-effect nuance.

One entry per job or trigger, in this order: what triggers it (schedule,
event, manual), the payload shape, concurrency behavior (can it run
overlapping instances, and what happens if it does), and the downstream
effect once it completes. A job description that omits concurrency
behavior leaves the most common on-call question — "is it safe to
re-trigger this?" — unanswered.

Name the owner per job, not just per system; a job with no named owner is
the one nobody fixes at 3 a.m. Keep remediation detail out — a job that's
misbehaving is a [runbook](../../operations/templates/runbook.md) concern, this
document describes intended behavior, not recovery.
