# `portfolio_compact`

Content contract for compact document type `portfolio_compact`.

The merged `docs-portfolio.md` is the compact form of the portfolio layer —
written at the repository root, sibling to `docs-portfolio/`, since its
target path must not collide with any of its own members' native paths
(the same reason `docs/product.md` sits outside `docs/product/`). It holds
the section-level orientation (portfolio boundary and member repositories)
followed by the repo inventory, system context, security posture,
operations, diligence index, and glossary, one `##` section per member
below. Decisions and epics stay separate, dynamically discovered indexes
(`docs-portfolio/decisions/README.md`, `docs-portfolio/epics/README.md`) —
this file links to them rather than folding them, since instance counts have
no fixed number to merge. Each section follows its member's own content
contract; the composed contract for this document lists the members this
project's manifest actually selected.

| Type | Must present | Keep out | Primary mode | Depth |
|---|---|---|---|---|
| portfolio_compact | section introduction, at-a-glance portfolio boundary, scope and boundaries, discovered repositories with role/owner/documentation state, repository/system boundaries with cross-repo flows and confidence-marked dependency edges, cross-repo security controls and gaps, shared operational dependencies and gaps, evidence map with confidence and follow-up, shared cross-repository terminology | member-internal call graphs, repo-local internals, member-level repetition of member-owned facts, heuristic edges without a confidence marker, unsupported verdicts, repository-local ADR duplication, direct source-file navigation | Orientation (Explanation/Reference in the member sections) | orientation |
