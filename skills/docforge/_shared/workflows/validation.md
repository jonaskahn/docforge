# Validation

Owns: staleness checks, manifest/provenance migration, the whole-tree audit,
the cross-document quality gate, and completion criteria.

## 6. Whole-tree gate

After all selected documents pass individually:

```sh
python3 runtime/cli/python/scaffold_docs.py \
node runtime/cli/js/scaffold_docs.js \
# bun  runtime/cli/js/scaffold_docs.js \
# deno run -A runtime/cli/js/scaffold_docs.js \
  --repo <repo> --manifest <repo>/.docforge/manifest.json --audit
```

The command exits nonzero for any defect. Apply the cold cross-document checks
inline. The checks owned by
[`../references/quality-bar.md`](../references/quality-bar.md) cover
reachability, onboarding, location, reviewer, stranger, duplication, and host
neutrality, plus README-specific checks: every section README links each
selected and materialized direct child (the `readme child coverage` finding),
and no section README routes readers into source files. A whole-tree discovery
that changes one artifact sends that artifact through its independent audit
again ([`writing.md`](writing.md)).

## Manifest and provenance

`.docforge/manifest.json` is the sole plan, state, provenance, and audit record.
Its schema version is `3.1`; there is no secondary runtime state file.
Manifest 3.0 and provenance 1.0 are migrated by `migrate_metadata` before
resume, revision, or provenance synchronization. Older or malformed metadata
requires re-grounding rather than a silent rewrite. When migration reports
`FAILED` for a document, the agent must regenerate that document's provenance
(status is already `in_progress`): re-ground claims, stamp concrete
provenance 2.0, lint, and audit before completion. See
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

`--document` accepts a manifest document `id` or `path` and limits both sync
and the staleness report to that entry (used by single-document update in
[`revision.md`](revision.md)).

`FRESH` means recorded sources still match; `PARTIAL` identifies `STALE`,
`MISSING`, or `NO_BLOB` sources for one section; `UNPARSEABLE` identifies
malformed document frontmatter; and `UNTRACKED` means provenance is absent,
empty, or legacy.
Synchronization reads every matching manifest path, including root documents,
and changes only each document's provenance section.

## Completion criteria

A document is `complete` only with a passing `cold-pass` audit
record. A run is complete only when every selected document is `complete` or
explicitly `skipped`, and the whole-tree gate above exits zero.

## 7. Dashboard auto-serve

Starting the dashboard is a **required** part of run completion, not an
optional nicety: when the whole-tree gate exits zero, run the dashboard so the
written documentation is immediately visible — this applies to every completed
`/docforge` (fresh start) and `/docforge-revise` run, and the dashboard URL is
reported in the final response:

1. **Never under `--plan-only`** — a dry run builds nothing and serves nothing.
2. **Skip when the invocation included `--no-dashboard`** — the run still
   completes; the user renders later with `/docforge-dashboard` or the
   internal `dashboard start`.
3. Run the dashboard lifecycle — preflight, metadata reconcile, signature,
   build (when changed), serve, open — via
   [`./dashboard.md`](dashboard.md) (internal to this cartridge; the optional
   `/docforge-dashboard` skill is only a thin entrypoint into it):
   `python3 runtime/cli/python/dashboard.py start --repo <repo>` (or the
   locked JS peer).
4. The first run takes longer: it scaffolds `.docforge/dashboard/`, runs
   `npm install`, and starts the detached dev server; later runs reuse the
   healthy recorded server when the signature is unchanged.
5. When Node.js 22+ / npm is unavailable or preflight fails, state the
   dashboard requirement and continue — a missing dashboard never blocks
   completion, but a successful run must print the `dashboard: <url>` line
   and name the URL in the final summary.
6. The dev server runs detached; `dashboard stop` shuts it down without
   affecting the written documentation or manifest state.

## Process completion & git state

Docforge maintains persistent records and ephemeral run state under `.docforge/`:
- **Tracked / Pushed to Git**: `.docforge/manifest.json`, `.docforge/flow-index.json`, `.docforge/.gitignore`.
- **Ignored by Git**: `.docforge/tmp/`, `.docforge/audits/`, `.docforge/scratch/`, `.docforge/backups/`, `.docforge/cache/`, `*.tmp`, `*.log`.

On fresh start or revision, `.docforge/.gitignore` is automatically created and maintained in `.docforge/`.
Upon process completion, run:

```sh
python3 runtime/cli/python/manage_manifest.py finish --repo <repo>
node runtime/cli/js/manage_manifest.js finish --repo <repo>
```

This ensures `.docforge/.gitignore` is up to date and cleans up ephemeral scratch directories (`tmp/`, `scratch/`), leaving only the persistent tracked files.
