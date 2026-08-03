# Api-rate-limits writing craft

Cite gateway, configuration, or specification evidence for every limit, header,
and 429 behavior. Link endpoint-specific authentication to `api-authentication`;
an absent documented limit is an unknown, not an unlimited contract.

**Preferred illustration:** Follow
[`../../../references/illustration.md`](../../../references/illustration.md); a table
for limit values by dimension, prose only for the retry contract.

State the limiting dimension first — per API key, per IP, per endpoint, per
account tier. Distinguish sustained rate from burst allowance where both
exist. Give the exact response
contract a caller can code against: status code, and every header the
caller reads (`Retry-After`, remaining-quota headers, reset timestamp) —
name the literal header, not "the appropriate header."

State what to do on a 429 as an imperative, not a description: back off for
the stated duration, then retry — not "clients should implement backoff."
If limits differ by plan or tier, give one table with tier as a column
rather than one prose paragraph per tier.
