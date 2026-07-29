# System-context (portfolio) writing craft

**Preferred illustration:** Follow
[`../references/illustration.md`](../references/illustration.md); a C4
Context-level Mermaid flowchart at portfolio scope — this repository's
`architecture-high-level.md` framing, applied across the member set.

Map repository and system boundaries at the portfolio level: which member
repos exist, what shared services or external systems the portfolio as a
whole borders, and which cross-repo flows cross those boundaries. Keep the
zoom at Context level — member-repo internals belong in that repo's own
`architecture-high-level.md` and `architecture-low-level.md`, not here; a
portfolio document that describes one member's internals in depth has lost
its own altitude.

State cross-repo flows as trigger → repos involved → outcome, one line
each, linking to each repo's owning flow document rather than re-deriving
the flow. This document orients a reader new to the whole portfolio, not a
reader already working inside one member.
