# Diligence collection

Before building Portfolio, discover the collection mechanically:

```sh
python scripts/discover_child_repos.py --root <parent-repository>
```

The result contains the parent, declared submodules, and detected nested
repositories not declared as submodules. A detected member always needs an
explicit inclusion decision; do not assume it is either in or out of scope.

For every included repository:

1. Check for a version-3 manifest and the selected baseline documents.
2. Run staleness checks for an existing baseline.
3. Build a missing Spine or Diligence baseline before representing the member
   as reviewed.
4. Record previous state, work performed, evidence, and remaining gaps in
   `docs-portfolio/repo-inventory.md`.

Prioritize undeclared detected members, customer-facing surfaces, and high-risk
dependencies. Never silently backfill a blind spot: the inventory should show
that it was found and how it was resolved.
