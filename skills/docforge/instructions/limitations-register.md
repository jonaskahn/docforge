# Limitations-register writing craft

**Preferred illustration:** Follow
[`../references/illustration.md`](../references/illustration.md); use tables
for comparable limits and prose for trigger, impact, workaround, and evidence.

Use one entry per observable limitation, and place it in exactly one of the register's
sections — a boundary test decides which, not a judgment call:

- **Known limitations** — built this way on purpose; a design trade-off, not a defect.
- **Known issues** — a defect under investigation, plausibly fixed later.
- **Not supported** — a capability a reasonable reader expects and will not find, with no
  fix in flight.
- **Scale and performance envelope** — a tested numeric boundary, not a behavior.

Within an entry, state trigger, impact, workaround, and evidence in that consistent order.
State impact the way a risk register states it — who is affected and how, not just what
breaks. Use frank language; do not soften impact, and do not turn a remediation hope into a
current fact — "not currently planned" is honest, "coming soon" is a promise this document
cannot keep. Order entries by how often a reader will hit them, not by discovery date or
file location.
