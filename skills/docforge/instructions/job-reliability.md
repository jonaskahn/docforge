# Job-reliability writing craft

**Preferred illustration:** Follow
[`../references/illustration.md`](../references/illustration.md); a table
per job class — retry, idempotency, timeout, backpressure, dead-letter,
replay — is the whole document.

State each reliability property as a concrete fact, not a category label:
retry count and backoff shape, not "retries"; the exact idempotency key or
mechanism, not "idempotent"; the timeout value and what happens on
timeout, not "times out." A job with no stated idempotency mechanism that
also retries is a duplicate-side-effect risk — say so plainly if that's the
actual state, rather than implying safety that isn't there.

State the dead-letter and replay path together: where failed jobs land,
and the actual procedure to replay them — a dead-letter queue with no
replay procedure is a place jobs go to be forgotten. Link job definitions
to [triggers-and-jobs.md](triggers-and-jobs.md) rather than restating
trigger/payload detail here; this document owns failure handling, not
job identity.
