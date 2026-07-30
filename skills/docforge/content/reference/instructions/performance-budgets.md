# Performance-budgets writing craft

**Preferred illustration:** Follow
[`../../../references/illustration.md`](../../../references/illustration.md); a table
of budget × measurement × degradation is the whole document.

One row per budget: the evidenced limit (CPU, GPU, memory, storage,
timing), how it was measured (load test, profiler, production
observation — name which), and what degrades when the budget is
approached or exceeded — an SRE error-budget framing applied to resource
limits rather than availability. Never state a target that hasn't been
measured; an invented number is worse than an honestly wide, evidenced
one.

Order by how often a reader hits the budget in practice, not by resource
type alphabetically. State the measurement's recency — a budget measured
two major versions ago may no longer hold; date it the way
limitations-register.md dates its review.
