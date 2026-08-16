# Portfolio diligence

Portfolio is the cross-repository tier: full Diligence for member repositories
plus the `docs-portfolio/` layer. Paths and the portfolio tree are owned by
[`docs-tree.md`](docs-tree.md); this file owns collection procedure and
cross-repository writing specifics.

## Collection procedure

Before building Portfolio, discover the collection mechanically:

```sh
python3 runtime/cli/python/discover_child_repos.py --root <parent-repository>
node runtime/cli/js/discover_child_repos.js --root <parent-repository>
# bun  runtime/cli/js/discover_child_repos.js --root <parent-repository>
# deno run -A runtime/cli/js/discover_child_repos.js --root <parent-repository>
```

The result contains the parent, declared submodules, and detected nested
repositories not declared as submodules, each tagged with its own tier
(`spine`, `diligence`, `portfolio`, or none) read from its own manifest. A
detected member always needs an explicit inclusion decision; do not assume
it is either in or out of scope.

For every included repository:

1. Check for a version-3.5 manifest, its tier, and the selected baseline
   documents.
2. Run staleness checks for an existing baseline.
3. Build a missing Spine or Diligence baseline before representing the member
   as reviewed.
4. Record previous state, work performed, evidence, and remaining gaps in
   `docs-portfolio/repo-inventory.md`.

Prioritize undeclared detected members, customer-facing surfaces, and high-risk
dependencies. Never silently backfill a blind spot: the inventory should show
that it was found and how it was resolved.

## Layout

**A Portfolio root is always `standard`.** Compact covers Spine and Diligence
only (see [`docs-tree.md`](docs-tree.md) "Compact layout"): folding the
collection layer into one file erases the per-member separation that is the
whole point of this tier. `init` and `reconcile` reject an explicit
`--layout compact` here, and force a *detected* compact layout to `standard`
as `decided_by: "tier-constraint"`.

Member repositories are documented at Spine or Diligence, each with its own
manifest and its own layout. A member may be compact while the collection root
is standard. Docforge never propagates a layout across a repository boundary.

## Readiness gate

Once inclusion is settled, check every included member's tier before
building anything under `docs-portfolio/`:

- If every included member is already at Diligence or Portfolio, the
  collection already qualifies — state that plainly and proceed.
- If any included member is below Diligence (Spine-only, or not generated
  at all), do not build the Portfolio layer yet. Name the lagging member(s)
  by path and direct the user to bring each to Diligence with its own
  separate, ordinary docforge run first — one repository at a time, never a
  combined pass — then re-run discovery. This is the repo-run-level version
  of the same per-document, no-bulk-dump cadence Docforge already follows
  inside a single repository.

## Cross-repository artifacts

Actual cross-repository decisions are dynamic documents under
`docs-portfolio/decisions/`. Cross-repository epics are dynamic documents under
`docs-portfolio/epics/`, added manually the same way (`manage_manifest.{py,js}
add
--type epic`) when a reviewer names an initiative and the repos it spans —
automatic inference across siblings is deferred.

- `README.md` is the platform one-pager and routes to every portfolio artifact.
- `repo-inventory.md` records every mechanically discovered member, membership
  evidence, baseline status, and review disposition.
- `system-context.md` shows the platform boundary, deployable members, shared
  dependencies (with coupling type and mapping/heuristic resolution),
  protocols, and important cross-repository flows. Optional identity mapping
  lives at `.metadata/portfolio/repo-identity.json` (see schema in the skill
  metadata); without it, edges resolve heuristically or are omitted. A
  cross-repo flow row is always two single-repo-grounded claims — each
  side's own flow document, itself grounded by that repo's own locked graph
  provider — joined by that same mapping/heuristic boundary match. Docforge
  never builds or requires a graph spanning repositories; see
  [`graph-sources.md`](graph/graph-sources.md)'s rule against synthesizing a
  combined "master graph," which applies here too.
- `security-posture.md` summarizes cross-cutting identity, secrets, encryption,
  network, dependency, logging, incident, and disclosure controls, linking to
  member evidence.
- `operations.md` owns platform environments, operational coupling, shared
  signals, recovery order, and external owner/SLO tokens.
- `diligence-index.md` maps review questions to evidence and records gaps and
  confidence.
- `glossary.md` owns terms shared across repositories.

Under time pressure, sequence orientation/inventory, system context,
dependencies/security, limitations, member architecture, then decisions. Do
not overstate intended architecture or hide known gaps; record evidence,
uncertainty, and remediation separately.
