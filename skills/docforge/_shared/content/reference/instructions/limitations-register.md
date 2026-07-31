# Limitations-register writing craft

Each limitation cites implementation, test, issue, or incident evidence and
names a review owner when established. Route remediable engineering debt to
`tech-debt-register`; preserve an unowned or unresolved limitation without
softening it into a roadmap promise.

**Preferred illustration:** Follow
[`../../../references/illustration.md`](../../../references/illustration.md); use tables
for comparable limits and prose for trigger, impact, workaround, and evidence.

Use one entry per observable limitation, and place it in exactly one of the register's
sections — a boundary test decides which, not a judgment call:

- **Known limitations** — built this way on purpose; a design trade-off, not a defect.
- **Known issues** — a defect under investigation, plausibly fixed later.
- **Not supported** — a capability a reasonable reader expects and will not find, with no
  fix in flight.
- **Scale and performance envelope** — a tested numeric boundary, not a behavior.

Within an entry, state trigger, impact, workaround, and evidence in that consistent order.
State impact in the reader's terms — "imports over 2 GB fail," not "the buffer is bounded
at 2 GB." Always give the workaround where one exists; a limitation without one reads as a
wall. Distinguish deliberate trade-offs from accidental gaps: a bound with stated reasoning
reads as judgment; the same bound unexplained reads as an oversight. Use frank language; do
not soften impact, and do not turn a remediation hope into a current fact — "not currently
planned" is honest, "coming soon" is a promise this document cannot keep. Date the review:
without a review date a reader cannot tell whether a missing entry means "no such
limitation" or "nobody has looked." Order entries by how often a reader will hit them, not
by discovery date or file location.
