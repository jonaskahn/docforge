# Api-rate-limits writing craft

**Preferred illustration:** Follow
[`../../../references/illustration.md`](../../../references/illustration.md); a table
for limit values by dimension, prose only for the retry contract.

State the limiting dimension first — per API key, per IP, per endpoint, per
account tier — because it changes what a caller must do to avoid the limit;
a number without its dimension is not actionable. Distinguish sustained
rate from burst allowance where both exist; a caller who only sees the
sustained number will misjudge a bursty workload. Give the exact response
contract a caller can code against: status code, and every header the
caller reads (`Retry-After`, remaining-quota headers, reset timestamp) —
name the literal header, not "the appropriate header."

State what to do on a 429 as an imperative, not a description: back off for
the stated duration, then retry — not "clients should implement backoff."
If limits differ by plan or tier, give one table with tier as a column
rather than one prose paragraph per tier; a reader comparing tiers should
not have to re-read prose three times.
