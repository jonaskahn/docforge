# Validation

Owns: staleness checks, manifest/provenance migration, the whole-tree audit,
the cross-document quality gate, and completion criteria.

## 6. Whole-tree gate

After all selected documents pass individually:

```sh
python runtime/cli/python/scaffold_docs.py \
node runtime/cli/js/scaffold_docs.js \
# bun  runtime/cli/js/scaffold_docs.js \
# deno run -A runtime/cli/js/scaffold_docs.js \
  --repo <repo> --manifest <repo>/.docforge/manifest.json --audit
```

The command exits nonzero for any defect. Then apply the cross-document checks
owned by [`../references/quality-bar.md`](../references/quality-bar.md):
reachability, onboarding, location, reviewer, stranger, duplication, and host
neutrality. A whole-tree discovery that changes one artifact sends that
artifact through its independent audit again
([`writing.md`](writing.md)).

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
python runtime/cli/python/check_staleness.py \
node runtime/cli/js/check_staleness.js \
# bun  runtime/cli/js/check_staleness.js \
# deno run -A runtime/cli/js/check_staleness.js \
  --manifest <repo>/.docforge/manifest.json

python runtime/cli/python/check_staleness.py \
node runtime/cli/js/check_staleness.js \
# bun  runtime/cli/js/check_staleness.js \
# deno run -A runtime/cli/js/check_staleness.js \
  --manifest <repo>/.docforge/manifest.json \
  --document docs/architecture/constraints.md --sync-provenance --json

python runtime/cli/python/check_staleness.py \
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

A document is `complete` only with a passing `subagent` or `cold-pass` audit
record. A run is complete only when every selected document is `complete` or
explicitly `skipped`, and the whole-tree gate above exits zero.
