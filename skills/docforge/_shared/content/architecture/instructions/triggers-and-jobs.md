# Triggers-and-jobs writing craft

- Trace each trigger, schedule, and concurrency rule to scheduler, queue,
  manifest, or code evidence.
- Name an owner only when established; link recovery procedures to their
  runbook and mark inferred downstream effects as unknown.
- One entry per job or trigger, in this order: what triggers it (schedule,
  event, manual), the payload shape, concurrency behavior (can it run
  overlapping instances, and what happens if it does), and the downstream
  effect once it completes.
- Name the owner per job, not just per system.
- Keep remediation detail out — a job that's misbehaving is a `runbook`
  concern, this document describes intended behavior, not recovery.

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

## Voice

- **Voice:** declarative present tense, strong active verbs, no hedging.
