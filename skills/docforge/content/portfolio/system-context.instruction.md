# System-context (portfolio) writing craft

**Preferred illustration:** Follow
[`../../references/illustration.md`](../../references/illustration.md); a C4
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

Before drawing the flowchart, resolve directed dependency edges between
members using this order: (1) `.metadata/portfolio/repo-identity.json`
mapping when present (`resolution: mapping`); (2) convention match of a
declared dependency identifier against a sibling's own package identity
(`resolution: heuristic`); (3) omit anything that resolves to neither —
never invent edges. Keep heuristic rows visually distinct via the
Resolution column. Coupling types include shared library, API contract,
event schema, and — when an `infrastructure-platform` member is present —
`provisions-for` / `deploys-into`. If edges and both tables outgrow one
reviewable file, promote to `system-context/README.md` +
`system-context/dependency-map.md` in the same pass that writes the
deep-dive (see `document-composition.md`); do not pre-split.
