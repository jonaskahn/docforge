# Validation

Owns: staleness checks, manifest/provenance migration, the whole-tree audit,
the cross-document quality gate, and completion criteria.

## Whole-tree gate

After all selected documents pass individually:

```sh
python3 runtime/cli/python/scaffold_docs.py \
node runtime/cli/js/scaffold_docs.js \
# bun  runtime/cli/js/scaffold_docs.js \
# deno run -A runtime/cli/js/scaffold_docs.js \
  --repo <repo> --manifest <repo>/.docforge/manifest.json --audit
```

The command exits nonzero for any defect. Apply the cold cross-document
checks inline. The checks owned by
[`../references/quality-bar.md`](../references/quality-bar.md) cover
reachability, onboarding, location, reviewer, stranger, duplication, and
host neutrality, plus README-specific checks: every section README links
each selected and materialized direct child outside the agent-context group
(the `readme child coverage` finding), every agent-context output contains
zero documentation references, no generated non-agent document mentions an
agent-context output (`agent-context outbound` and `agent-context leak`,
respectively), and no section README routes readers into source files.
Plain source/configuration paths and verified commands remain valid inside
agent-context outputs. A whole-tree discovery that changes one artifact
sends that artifact through its independent audit again
([`writing.md`](writing.md)).

Unmanaged docs (`project.unmanaged_docs`) and everything under
`docs/_archive/` (or `docs-portfolio/_archive/`) are known, never findings:
the audit's `unexpected` check skips them, and the gate neither requires
nor offers anything for them. The gate's exit code reflects real defects
only.

## Manifest and provenance

`.docforge/manifest.json` is the sole plan, state, provenance, and audit
record. Its schema version is `3.9`. There is no second manifest or shadow
state file — `.docforge/flow-index.json` (the flow ledger) and the
provenance sidecars are the only other persistent records.

**Migration is unconditional.** Every invocation that touches an existing
manifest — every `/docforge-revise` path regardless of scope argument,
single-document update included, and `/docforge` planning when a manifest
already exists — begins with an explicit `migrate_metadata.{py,js}` run
covering both manifest schema and provenance storage. Migration is
idempotent, so an already-current manifest reports a clean no-op; that
cheapness is why the run is unconditional, never "when needed".

Manifest 3.8 (and 3.7 / 3.6 / 3.5 / 3.4 / 3.3 / 3.2 / 3.1 / 3.0 / provenance 1.0) are migrated by
`migrate_metadata.{py,js}`
(see [`../runtime/manifest/README.md`](../runtime/manifest/README.md)) before
resume, revision, or provenance synchronization — every run,
version-agnostic and idempotent. It also seeds each document's
catalog-owned `description` from the catalog `summary`, normalizes
`provenance_storage` to `json` (moving any surviving inline frontmatter
into the sidecars), the project's `unmanaged_docs` list (empty by default),
and the project's `scale` record (`decided_by: "detected"` from live
detection when absent; a present record is never overwritten — its
measurement `signals` are refreshed on upgrade with the 3.7 dependency and
flow fields, while `class`, `layout`, and `decided_by` stand). A legacy
manifest of any pre-3.0 version (1.1 `project_context` / `document_groups`,
2.0 flat `documents` with overlays, or another shape) is re-registered by
the same command: written documents are adopted as `generated` with
provenance 2.1, bodies and source hashes preserved, and plan entries kept;
adopted documents are never `complete` (no independent audit survived) and
still need the revision path to re-ground, lint, and audit them. Older or
malformed metadata requires re-grounding rather than a silent rewrite. When
migration reports `FAILED` for a document, the agent must regenerate that
document's provenance (status is already `in_progress`): re-ground claims,
stamp concrete provenance 2.1, lint, and audit before completion. See
[`../references/provenance-tracking.md`](../references/provenance-tracking.md).

Check staleness with:

```sh
python3 runtime/cli/python/check_staleness.py \
node runtime/cli/js/check_staleness.js \
# bun  runtime/cli/js/check_staleness.js \
# deno run -A runtime/cli/js/check_staleness.js \
  --manifest <repo>/.docforge/manifest.json

python3 runtime/cli/python/check_staleness.py \
node runtime/cli/js/check_staleness.js \
# bun  runtime/cli/js/check_staleness.js \
# deno run -A runtime/cli/js/check_staleness.js \
  --manifest <repo>/.docforge/manifest.json \
  --document docs/architecture/constraints.md --sync-provenance --json

python3 runtime/cli/python/check_staleness.py \
node runtime/cli/js/check_staleness.js \
# bun  runtime/cli/js/check_staleness.js \
# deno run -A runtime/cli/js/check_staleness.js \
  --manifest <repo>/.docforge/manifest.json \
  --section configuration --sync-provenance
```

`--document` accepts a manifest document `id` or `path` and limits both
sync and the staleness report to that entry (used by single-document update
in [`revision.md`](revision.md)).

Verdicts:

- `FRESH` — recorded sources still match.
- `PARTIAL` — identifies `STALE`, `MISSING`, `NO_BLOB`, or the non-blocking
  `COSMETIC` sources for one section (a `COSMETIC` source's normalized or
  range-scoped hash still matches; it does not require re-grounding).
- `UNPARSEABLE` — malformed document frontmatter.
- `UNTRACKED` — provenance is absent, empty, or legacy.

Synchronization reads every matching manifest path, including root
documents, and changes only each document's provenance section — the folder
sidecar entry, where a document still carrying inline frontmatter from
before the sidecar store is moved automatically.

## Completion criteria

A document is `complete` only with a passing `cold-pass` audit record. A
run is complete only when every selected document is `complete`, explicitly
`skipped`, or `retired` (out of scope — the entry is preserved, the file
moved or deleted by the approved retirement step; a `retired` document
carries no whole-tree-gate coverage expectations, exactly like `skipped`),
and the whole-tree gate above exits zero.

## Dashboard auto-serve

Starting the dashboard is a **required** part of run completion, not an
optional nicety: when the whole-tree gate exits zero, run the dashboard so
the written documentation is immediately visible — this applies to every completed
`/docforge` (fresh start) and `/docforge-revise` run, and the dashboard URL is
reported in the final response:

1. **Never under `--plan-only`** — a dry run builds nothing and serves
   nothing.
2. **Skip when the invocation included `--no-dashboard`** — the run still
   completes; the user renders later with `/docforge-dashboard` or the
   internal `dashboard.{py,js} start`.
3. **An agent-context-only run has nothing to render** — when every
   selected document is in the `agent-context` group, skip items 5-8 and
   say so once: the agent documents are read as files, not browsed, and no
   human-facing documentation exists for a site to show. `dashboard scan`
   reports this as `agent-context only`, which is a scope fact, not a
   defect to revise. The run still completes.
4. **Compact layout offers instead of serves** — when
   `project.scale.layout == "compact"` and neither `--plan-only` nor
   `--no-dashboard` was given, do not run items 5-8 automatically; append
   one offer line to the final response ("Compact layout — start the local
   dashboard? Reply yes, or run `/docforge-dashboard` later."). An explicit
   yes in the same turn runs items 5-8 unchanged.
5. Run the dashboard lifecycle — preflight, metadata reconcile, signature,
   build (when changed), serve, open — via [`./dashboard.md`](dashboard.md)
   (internal to this cartridge; the optional `/docforge-dashboard` skill is
   only a thin entrypoint into it):
   `python3 runtime/cli/python/dashboard.py start --repo <repo>` (or the
   locked JS peer).
6. The first run takes longer: it scaffolds `.docforge/dashboard/`, runs
   `npm install`, and starts the detached dev server; later runs reuse the
   healthy recorded server when the signature is unchanged.
7. When Node.js 22+ / npm is unavailable or preflight fails, state the
   dashboard requirement and continue — a missing dashboard never blocks
   completion, but a successful run must print the `dashboard: <url>` line
   and name the URL in the final summary.
8. The dev server runs detached; `dashboard.{py,js} stop` shuts it down
   without affecting the written documentation or manifest state (see
   [`../runtime/dashboard/README.md`](../runtime/dashboard/README.md)).

## Process completion & git state

Docforge maintains persistent records and ephemeral run state under
`.docforge/`:

- **Tracked / Pushed to Git**: `.docforge/manifest.json`,
  `.docforge/flow-index.json`, `.docforge/provenance/`,
  `.docforge/.gitignore`.
- **Ignored by Git**: `.docforge/tmp/`, `.docforge/audits/`,
  `.docforge/scratch/`, `.docforge/backups/`, `.docforge/cache/`,
  `.docforge/obsolete/`, `.docforge/dashboard/`, `*.tmp`, `*.log`.

On fresh start or revision, `.docforge/.gitignore` is automatically created
and maintained in `.docforge/`. Upon process completion, run:

```sh
python3 runtime/cli/python/manage_manifest.py finish --repo <repo>
node runtime/cli/js/manage_manifest.js finish --repo <repo>
```

This ensures `.docforge/.gitignore` is up to date and cleans up ephemeral
scratch directories (`tmp/`, `scratch/`), leaving only the persistent
tracked files.
