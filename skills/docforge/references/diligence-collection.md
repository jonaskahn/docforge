# Diligence collection — multi-repo discovery and gap-check before the portfolio layer

**Applies when:** a Tier 3 / multi-repo diligence job begins. `references/diligence.md` describes the portfolio layer but assumes every member repo already carries its own tier-appropriate docs; assume the opposite by default — verify the collection before building anything on top of it.

## Why this can't be a hand-typed list

A diligence review is adversarial-by-default: the reviewer is specifically looking for what the team missed. A submodule added six months ago and never mentioned in the kickoff conversation is exactly that kind of gap, and a repo nested by copy or `git subtree` rather than a proper submodule hides even from `git submodule status`. Discovery has to be mechanical, not remembered.

## Assemble the collection

Run:
```
python scripts/discover_repos.py --root <parent-repo-path>
```
This returns every repo in scope, in three categories:

1. **The parent** — the repo you were pointed at.
2. **Declared children** — every path listed in `.gitmodules`, resolved via `git submodule status` where possible.
3. **Detected children** — any directory anywhere under the root that contains its own `.git` (a directory, or a `gitdir:` pointer file, which is how a submodule's working copy is actually linked) and is **not** listed in `.gitmodules`. This is the category that matters most: it surfaces vendored copies, `git subtree`-merged code, or a submodule that was cloned by hand instead of registered properly.

A detected child repo always needs a judgment call before it's treated as in-scope or out-of-scope — do not assume either. Ask whoever owns the parent repo whether it is a legitimate part of the system or accidental clutter that should be excluded from the review (and, separately, from the repository itself).

## This applies beyond diligence, at lower weight

Even outside a formal diligence job, run the same discovery check before generating or updating docs for any repo that might have children — it's a cheap sanity check the rest of the time ("this repo has 2 submodules; are they in scope for what you're asking?"), and load-bearing the moment the job becomes a multi-repo review.

## Gap-check every member before building the portfolio layer

For each repo the discovery step returns:

1. Look for `docs/.docforge/manifest.json` and `docs/architecture/overview.md`.
   - Both present → this repo already has a docforge baseline. Run `check_provenance.py` against it as usual (see `provenance-tracking.md`) rather than treating it as new.
   - Either missing → this repo has never been through docforge. **Generate its baseline first** — the full Step 1–6 workflow, plus the BA/PO audience overlays (Step 3) if that documentation is in scope for the review — before the collection is considered ready for the portfolio layer.
2. Do not proceed to `docs-portfolio/` with a known gap in the collection. An unreviewed repo silently included looks assessed when it was not, which is worse than one honestly flagged as missing.
3. Record every repo's status in `docs-portfolio/repo-inventory.md` (new file, sits beside docforge's `README.md` and `system-context.md` in the portfolio layer) — see the table format below.

## Sequencing under time pressure

Backfilling several repos at once is expensive. Prioritize by exposure, not alphabetically or by convenience:

1. **Any detected (undeclared) child repo first** — its invisibility to `.gitmodules` is itself a finding worth surfacing early, independent of what turns out to be inside it.
2. Repos that ship a customer-facing surface (an API service, a published package) before purely internal tooling.
3. Within a single repo, follow docforge's own priority order from `diligence.md`'s "Preparing under time pressure": README/context, dependency inventory, security posture, limitations, architecture overview, decision records.

## `docs-portfolio/repo-inventory.md`

Extends docforge's portfolio tree; doesn't replace anything already defined there.

```markdown
# Repo inventory

| Repo | Path | Membership | Docforge status (before this review) | Backfilled this review? |
|---|---|---|---|---|
| pluggy-api | services/pluggy-api | declared (submodule) | Tier 2 | no |
| legacy-etl | vendor/legacy-etl | **detected — not in .gitmodules** | none | yes — Tier 1 |
```

A reviewer reads this table before `system-context.md`. It is the disclosure that the portfolio's own map might have had blind spots, stated plainly as found-and-closed rather than silently patched — which is exactly the honest posture `diligence.md` argues increases reviewer confidence.

## Anti-patterns

- Building the portfolio layer against whatever repos happen to be checked out locally, without running discovery — silently drops anything not currently cloned to this machine.
- Treating a detected nested repo as automatically in scope, or automatically excluded, without asking — both directions are guesses dressed as decisions.
- Backfilling a missing repo's docs and merging it into the portfolio without recording in `repo-inventory.md` that it was a gap — the value of finding your own blind spot is destroyed if the record doesn't show it was one.
