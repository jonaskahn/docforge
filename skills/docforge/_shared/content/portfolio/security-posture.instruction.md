# Security-posture / portfolio-operations writing craft

Covers both `portfolio_security` and `portfolio_operations` — they share one
content-catalog row (cross-repo controls, gaps, shared dependencies,
operational coupling) and differ only in which half they emphasize.

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

## Illustration

- **Form:** a table per repository is primary; a Mermaid `flowchart` only
  when shared dependency or coupling relationships among three or more
  repositories need it.
- **Renders:** a coverage table (control × repo), or (when warranted) the
  shared dependency graph across repos.
- **Trigger:** the flowchart only past three repositories sharing a
  coupling relationship worth tracing together — per
  [`../../references/illustration.md`](../../references/illustration.md)'s
  deep-dive budget.

## Connections

| This document owns | Links to | Because |
|---|---|---|
| Cross-repo controls, gaps, shared dependencies, operational coupling | each member repo's own `threat-model` or `observability` document | member-internal findings are owned there; this document owns only the cross-repo seam |
| A shared dependency also named in a member's `dependencies-inventory` | that member's `dependencies-inventory` | this document adds the cross-repo blast radius; the member document owns its own criticality judgment |
| An unresolved cross-repo gap | `diligence-index` | tracks the confidence gap until a member closes it |
