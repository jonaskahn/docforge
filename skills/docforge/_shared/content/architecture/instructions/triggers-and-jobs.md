# Triggers-and-jobs writing craft

Trace each trigger, schedule, and concurrency rule to scheduler, queue, manifest,
or code evidence. Name an owner only when established; link recovery procedures
to their runbook and mark inferred downstream effects as unknown.

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

## Illustration

- **Form:** a table per job — trigger, payload, schedule, ownership; prose
  only for downstream-effect nuance.
- **Renders:** one row per job with its concurrency behavior stated
  explicitly.
- **Trigger:** never a diagram for the register itself; per
  [`illustration.md`](../../../references/illustration.md) this stays tabular.

## Connections

| This document owns | Links to | Because |
|---|---|---|
| Trigger, payload, scheduling, concurrency, ownership, downstream effects | `operations` runbooks | remediation for a misbehaving job is owned there; this document describes intended behavior only |
| A downstream effect that starts a flow | the relevant `flow` document | avoids re-deriving flow steps inside a job description |
| A data-shape guarantee in the payload | `dataset` or `data-flow` | schema/lineage detail is owned there, linked not restated |
