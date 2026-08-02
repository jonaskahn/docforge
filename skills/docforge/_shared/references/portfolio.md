# Portfolio diligence

Portfolio is the cross-repository tier: full Diligence for member repositories
plus the `docs-portfolio/` layer. Paths and the portfolio tree are owned by
[`docs-tree.md`](docs-tree.md); this file owns collection procedure and
cross-repository writing specifics.

## Collection procedure

Before building Portfolio, discover the collection mechanically:

```sh
python runtime/cli/python/discover_child_repos.py --root <parent-repository>
node runtime/cli/js/discover_child_repos.js --root <parent-repository>
# bun  runtime/cli/js/discover_child_repos.js --root <parent-repository>
# deno run -A runtime/cli/js/discover_child_repos.js --root <parent-repository>
```

The result contains the parent, declared submodules, and detected nested
repositories not declared as submodules. A detected member always needs an
explicit inclusion decision; do not assume it is either in or out of scope.

For every included repository:

1. Check for a version-3.1 manifest and the selected baseline documents.
2. Run staleness checks for an existing baseline.
3. Build a missing Spine or Diligence baseline before representing the member
   as reviewed.
4. Record previous state, work performed, evidence, and remaining gaps in
   `docs-portfolio/repo-inventory.md`.

Prioritize undeclared detected members, customer-facing surfaces, and high-risk
dependencies. Never silently backfill a blind spot: the inventory should show
that it was found and how it was resolved.

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
  metadata); without it, edges resolve heuristically or are omitted.
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
