# Repo inventory

_Last generated: {{YYYY-MM-DD}}_

Every repo in scope for this diligence review, assembled by `scripts/discover_child_repos.py` — declared submodules and any nested repo detected on disk without being declared. See `../../references/diligence-collection.md` for how this table is built and why detected entries always need a human judgment call before inclusion.

| Repo | Path | Membership | Docforge status (before this review) | Backfilled this review? |
|---|---|---|---|---|
| {{repo name}} | {{path relative to portfolio root}} | {{declared (submodule) / detected — not in .gitmodules / parent}} | {{none / tier 1 / tier 2 / baseline + provenance}} | {{yes — tier X / no}} |

<!-- One row per member of the collection, including the parent. Never omit
     a detected-but-excluded repo from this table — record it as excluded
     and why, rather than leaving no trace it was considered. -->
