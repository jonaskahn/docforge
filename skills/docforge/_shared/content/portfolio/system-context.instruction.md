# System-context (portfolio) writing craft

For every dependency edge, record repository or source locator, resolution method,
and separate confidence; heuristic matching never appears confirmed. Explain each
material diagrammed boundary and exception in prose, linking member-owned flows
instead of synthesizing execution sequences.

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

Identify which flows cross a repo boundary in the first place the same
mechanical way dependency edges are identified — never by querying a graph
across repositories, since no such graph exists: `flow_edges` from
`discover_child_repos` resolves them in order — (1) an explicit `flows` row
in `.metadata/portfolio/repo-identity.json` (`resolution: mapping`); (2) a
literal signature match between one member's own exposed entry point
(`.docforge/flow-index.json`'s `entry_ref.signature`, e.g. `"POST /orders"`)
and another member's own recorded flow evidence (`resolution: heuristic`);
(3) no match — omit, never invent a cross-repo flow. Keep heuristic rows
visually distinct, same as dependency edges.

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

## Illustration

- **Form:** a C4 Context-level Mermaid `flowchart` at portfolio scope — this
  repository's `architecture-high-level.md` framing, applied across the
  member set.
- **Renders:** each member repo as a node, shared services/external systems
  at the boundary, and cross-repo flows as labeled edges with their
  resolution method.
- **Trigger:** always for this document type — portfolio-wide boundaries are
  the point — within
  [`../../references/illustration.md`](../../references/illustration.md)'s
  deep-dive budget.

## Connections

| This document owns | Links to | Because |
|---|---|---|
| Portfolio-level repo/system boundaries, cross-repo flows, dependency edges and their resolution | each member's own `architecture-high-level` | member-internal container detail is owned there; this document only borders it |
| A cross-repo flow's steps | that flow's owning member document | this document states trigger → repos → outcome only; step detail is never re-derived here |
| A repo not yet resolved to an identity mapping | `repo-inventory` | inventory evidence is owned there; this document consumes it to draw edges |
