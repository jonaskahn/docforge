# Writing `docs-portfolio.md`

The compact portfolio file — exists only at Portfolio tier. Written at the
repository root (sibling to `docs-portfolio/`, `docs/`, `README.md`) rather
than as `docs-portfolio/README.md`, the same way `docs/product.md` sits
outside `docs/product/`: the target path must not collide with any of its
own members' native paths. Write one `##` section per member the manifest
selected, in this reading order, grounding each section from the evidence
its member contract requires:

1. `## At a glance` — folder-index orientation (portfolio boundary, member
   repositories). Link to the decisions index
   (`docs-portfolio/decisions/README.md`) and the epics index
   (`docs-portfolio/epics/README.md`) in Scope and boundaries — both stay
   separate, dynamically discovered indexes and are never folded in here.
2. `## Repository inventory` — `repo-inventory` (every repository in scope,
   assembled from declared submodules and detected nested repositories;
   role, owner token, documentation state, evidence). Never omit a
   detected-but-excluded repo — record it as excluded and why.
3. `## System context` — `system-context` (repository/system boundaries,
   shared services, cross-repo flows, directed dependency edges with
   coupling type and resolution confidence). Never present a heuristic edge
   without its confidence marker.
4. `## Security posture` — `security-posture` (cross-repo controls, gaps,
   shared dependencies, operational coupling). Link each member's own
   threat model for local detail; do not duplicate it.
5. `## Operations` — `portfolio-operations` (shared operational
   dependencies and their portfolio-wide blast radius if they degrade).
   Link each member's own observability/deployment docs for local detail;
   do not duplicate it.
6. `## Diligence index` — `diligence-index` (evidence map: claim, evidence,
   confidence, gap/follow-up, per area). Never record an unsupported
   verdict.
7. `## Glossary` — `portfolio-glossary` (terms shared across member
   repositories, or likely to confuse a reader moving between them;
   repo-local terms stay in that repo's own glossary).

Ground each section from the repository evidence cited in provenance — one
provenance `sections[]` entry per `##` heading. Do not add sections beyond
what the manifest's `compact_members` for this document actually lists, and
do not route readers into source files.
