# Disaster-recovery writing craft

**Preferred illustration:** Follow
[`../references/illustration.md`](../references/illustration.md); prose and
an ordered command list — this is a runbook shape, not a diagram.

State RTO (how long recovery may take) and RPO (how much data loss is
acceptable) per scenario, as numbers, not aspirations — an unevidenced
target is worse than an honestly wide one. Give explicit stop conditions:
what state means "recovery is failing, escalate" versus "keep going" — a
recovery procedure with no stop condition risks compounding the original
failure. Order recovery steps by dependency, not by convenience; a
downstream service brought up before its data store is not actually
recovered.

Every scenario ends the same way: a verification step that proves recovery
succeeded, not just that the commands ran. State the data-loss boundary
explicitly — the exact point in time data recovers to — rather than
implying "nothing was lost." Keep ordinary deploy steps out; this document
is for the day deployment already failed.
