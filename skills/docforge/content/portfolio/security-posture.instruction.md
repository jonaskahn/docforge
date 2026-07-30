# Security-posture / portfolio-operations writing craft

Covers both `portfolio_security` and `portfolio_operations` — they share one
content-catalog row (cross-repo controls, gaps, shared dependencies,
operational coupling) and differ only in which half they emphasize.

**Preferred illustration:** Follow
[`../../references/illustration.md`](../../references/illustration.md); a
Mermaid flowchart only when shared dependency or coupling relationships
among three or more repositories need it — otherwise a table per
repository.

Write at the seam between repositories, not inside any one of them: what
control, dependency, or operational responsibility is shared across
member repos, and what gap exists because no single repo owns it. A
finding that is really about one repository's internals belongs in that
repo's own `threat-model.md` or `observability.md` — link to it, don't
duplicate it here. State each gap's blast radius across the portfolio, not
just its local severity; a shared dependency's failure mode matters more
here than in any single member's view.

For security posture specifically: name the control, which repos it
covers, and which don't have it yet — a coverage table, not a narrative.
For operational coupling: name the shared operational dependency (a queue,
a shared datastore, a shared on-call rotation) and what happens across the
portfolio when it degrades. Never repeat member-level detail that adds no
cross-repo information — that repetition is exactly what this document
type exists to avoid.
