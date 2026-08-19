# Portfolio writing craft

Writing-craft instructions for `portfolio` group documents. Routes:

- `portfolio_diligence_index` → [Diligence-index](#diligence-index-writing-craft)
- `epic` → [Epic (portfolio)](#epic-portfolio-writing-craft)
- `portfolio_repo_inventory` → [Repo-inventory](#repo-inventory-writing-craft)
- `portfolio_security`, `portfolio_operations` → [Security-posture / portfolio-operations](#security-posture--portfolio-operations-writing-craft)
- `portfolio_system_context` → [System-context (portfolio)](#system-context-portfolio-writing-craft)

## Voice and linking craft

Voice for this group is owned by [`voice.md`](../../references/voice.md):
executive, value and risk before mechanism. Name what a member document
owns before linking it ("the member's internal steps are owned there,"
never "see the flow document"). What each side of a link owns, and why it
is linked rather than restated, is each contract's `## Owns / links` table,
not this section.

## Diligence-index writing craft

Each evidence cell links to a member document or repository-relative source path,
not merely an area name. For every partial or unsupported claim, state a concrete
follow-up and its evidenced owner token or `undetermined`; never promote it to a
verdict without support.

One row per claim under review: the claim, the evidence found for it, a
confidence level, and the gap remaining if confidence is anything less than
high. State confidence honestly on a small, fixed scale (for example
confirmed / partial / unsupported) rather than a prose hedge that dodges
the question. A claim with no evidence gets "unsupported" and a follow-up
action, not a soft rewrite into something the evidence happens to support.

Group by the area under diligence (architecture, security, operations,
dependencies) so a reader assessing one dimension doesn't have to scan the
whole table. Never render a verdict — pass/fail, safe/unsafe — this
document maps evidence and gaps.

## Illustration

- **Form:** a table is the whole document — this is an evidence map, not a
  narrative.
- **Renders:** nothing beyond the table; no diagram, ever.
- **Trigger:** never — per
  [`../../references/illustration.md`](../../references/illustration.md).

## Epic (portfolio) writing craft

Ground each repository contribution and handoff in member documentation or history
evidence. Mark an unproved sequence as an open gap; assign an owner token only
when evidenced, otherwise use `undetermined` and link the follow-up in
`diligence-index`.

An epic names a cross-repository initiative. State the outcome first, then the
member repos it spans with each repo's owning flow/feature and component, then
the cross-repo sequence that ties them together. Link to member documents by
path; do not restate member-internal call graphs or invent scope.

Open gaps stay explicit — missing owners, unresolved handoffs, or undetermined
sequencing. Epics are added
manually via `manage_manifest add --type epic` (agent-asserted
`discovered_epic`), mirroring portfolio decisions.

## Illustration

- **Form:** a `sequenceDiagram` that spans the member repos in initiative
  order.
- **Renders:** each member repo as a participant and each cross-repo handoff
  as a labeled call, in the order the initiative actually proceeds.
- **Trigger:** always for this document type — the cross-repo sequence is the
  point — within
  [`../../references/illustration.md`](../../references/illustration.md)'s
  5-participant limit.

## Repo-inventory writing craft

For every discovered member, record relative path, membership evidence, explicit
inclusion or exclusion decision and reason, pre-review baseline, work performed,
and remaining gap. Include role and owner only when directly supported; preserve
`undetermined` and link unresolved ownership to `diligence-index`.

One row per discovered repository: its role in the portfolio, an owner token
(team or individual accountable for it), documentation state (undocumented,
spine, diligence, portfolio-aware), and the evidence for each field — where
`discover_child_repos` or the manifest actually found this repository, not a
hand-typed addition. A row with no evidence is a defect; every repository
listed must trace to a discovery mechanism this document can name.

Never fill a gap with a plausible guess. If a repository's role or owner is
undetermined, state "undetermined" and let `diligence-index` carry the
resulting confidence gap — this document is the exhaustive lookup, not the
place judgment calls get resolved.

## Illustration

- **Form:** a Markdown table only — this is a Reference-depth lookup, not a
  narrative.
- **Renders:** nothing beyond the table; no relationship diagram, even when
  repositories depend on each other — that belongs to `system-context`.
- **Trigger:** never — per
  [`../../references/illustration.md`](../../references/illustration.md),
  reference documents default to tables.

## Security-posture / portfolio-operations writing craft

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
cross-repo information.

Every shared control, gap, or coupling row names assessed repositories, status
(`covered`, `absent`, `not applicable`, or `unknown`), evidence and as-of date,
cross-repo blast radius, and accountable follow-up. Assessment scope is not
coverage: state what was not reviewed. Link member security or operations
documents for local evidence, and link the diligence index whenever ownership,
evidence, or risk disposition remains unresolved.

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

## System-context (portfolio) writing craft

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
