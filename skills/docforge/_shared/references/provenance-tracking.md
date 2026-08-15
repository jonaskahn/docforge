# Provenance tracking

This file owns metadata format, validation, and staleness semantics.

## Storage

Every generated document is **frontmatter-free**: `project.provenance_storage`
in `.docforge/manifest.json` is always `"json"`, and public identity plus
provenance live in one git-tracked sidecar per docs folder,
`.docforge/provenance/<folder>.json` (`docs/architecture` →
`docs/architecture.json`, repo-root files → `root.json`):

```json
{
  "schema": "1.0",
  "folder": "docs/architecture",
  "files": {
    "constraints.md": {
      "id": "architecture_constraints",
      "title": "Architecture Constraints",
      "description": "One-liner.",
      "provenance": { "schema": "2.1", "doc_id": "architecture_constraints", "...": "…" }
    }
  }
}
```

The `provenance` object is the exact block described below. A document
written before the sidecar store still carries inline frontmatter until
something moves it: `migrate_metadata.{py,js}` moves it (dry-run preview
first) and `check_staleness.{py,js} --sync-provenance` moves any straggler it
meets. **Old-schema metadata is always detected explicitly** — a schema-less
(legacy) or schema-1.0 / `tool_version` (obsolete) block, wherever it is
found, is reported as `legacy` / `obsolete`, never treated as current, and is
never silently moved; there is no opt-in or opt-out. Such documents must pass
through `migrate_metadata.{py,js}` (schema conversion) before the sidecar
move.

All readers (lint, staleness, audit, dashboard, plan) resolve provenance the
same way: the sidecar entry first; a document with no entry falls back to
reading inline frontmatter, reported as `inline` so lint flags it as pending
migration rather than treating it as current.

## The provenance object

Restricted YAML provenance 2.1, the sidecar entry's `provenance` field
(a pre-migration document instead carries this at byte one of the file, under
a `docforge_provenance` key):

```yaml
schema: "2.1"
doc_id: "architecture_constraints"
path: "docs/architecture/constraints.md"
generated_at: "2026-07-27T09:12:44Z"
generator:
  name: "docforge"
  version: "2.18.0"
tier: "diligence"
target_depth: "deep-dive"
git_commit: "9f1c0aa4e2b7d3915c6f0b8ad24e7c31b5a0e6d2"
content_hash: "sha256:0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
graph:
  provider: "gitnexus"
  flow: "native"
sections:
  - id: "ceilings"
    sources:
      - path: "src/server.js"
        git_blob: "3b18e512dba79e4c8300dd08aeb37f8e728b8dad"
        git_blob_normalized: "9af3c1de1b6f0a7c4e2d8b5f0163a2c9e8d7f4b1"
        evidence_range:
          start: "40"
          end: "58"
        range_blob: "c81e728d9d4c2f636f067f89cc14862c6c47f4b7"
        role: "code"
    unresolved: []
```

The codec in `runtime/cli/python/provenance_frontmatter.py` / `runtime/cli/js/provenance_frontmatter.js` owns parsing (both the
sidecar's plain JSON and a pre-migration document's restricted YAML); the
sidecar store in `runtime/cli/python/provenance_store.py` /
`runtime/cli/js/provenance_store.js` owns reading and writing the sidecar
itself. A pre-migration document's inline block is a deterministic YAML
subset: 2-space indent, fixed key order, and every scalar double-quoted, with
anchors, aliases, block scalars, multi-document markers, and non-empty flow
collections all rejected. `schema` is `2.0` or `2.1`; new writes stamp `2.1`,
and existing `2.0` documents never need to change.

`doc_id` and `path` identify the manifest entry. `generated_at` and optional
`git_commit` identify the write activity. `generator.name` and
`generator.version` identify the generator. Optional `content_hash` is a SHA-256 of the
Markdown body (`sha256:<64 hex>`). Optional `review` records
`mode`, `verdict`, and `report` from the independent audit. `tier` and
`target_depth` carry the content contract. `graph.provider` names the selected
provider and `graph.flow` is `native`, `derived`, or `none`. `graph_snapshot`
is not part of provenance 2.1.

Written documents also carry a **public** identity beside `provenance` in the
sidecar entry (or above `docforge_provenance` in a pre-migration document's
frontmatter): `id`, `title`, and `description` (a reader-facing
one-liner of at most 160 characters). `description` is catalog-owned — seeded
from the manifest (catalog `summary`) at init / migrate / reconcile and kept
in sync with the manifest by the dashboard; lint rejects written documents
without a non-empty description.

Each section `id` is a Markdown heading anchor. Its sources use repository-
relative file paths, a Git blob hash of the working-tree bytes, and one role:
`code`, `config`, `manifest`, `doc`, `test`, or `history`. `unresolved` lists
typed external tokens intentionally retained in that section.

Optional per-source `git_blob_normalized` is a whitespace/line-ending-
normalized whole-file blob hash (`^[0-9a-f]{40}$`); optional `evidence_range`
(`{start, end}`, 1-indexed inclusive) plus `range_blob` scope a source to a
specific line span. Both exist purely so `check_staleness` can prove a raw
blob mismatch is cosmetic rather than a real change — see "Staleness results"
below. Stamp both with `hash_evidence.{py,js}` (see
[`../runtime/manifest/README.md`](../runtime/manifest/README.md)), never by
hand: unlike `git_blob`, which matches ubiquitous `git hash-object`, these two
have no standard-tool equivalent, so an ad hoc reimplementation risks quietly
diverging from what `check_staleness` recomputes later. Malformed values are
treated as absent, never as a lint defect.

Templates and planned manifest entries use explicit string tokens such as
`<DOC_ID>` and `<GENERATED_AT>` for values unavailable before writing. These
tokens and an empty `sections` array are valid only while a document remains
planned or in progress. Generated, needs-review, and complete documents require
concrete values and at least one section.

Exceptions are `AGENTS.md`, fixed shims such as `CLAUDE.md` and
`CLAUDE.local.md`, and machine JSON configuration. Their provenance is stored
only in the corresponding manifest document entry.

## Migration

JSON provenance 1.0 (`tool_version`, schema `1.0`) and schema-less pre-2.0
YAML (including `doc` / `graph_snapshot` shapes) are obsolete. Run:

```sh
python3 runtime/cli/python/migrate_metadata.py --repo <repo>
node runtime/cli/js/migrate_metadata.js --repo <repo>
# bun  runtime/cli/js/migrate_metadata.js --repo <repo>
# deno run -A runtime/cli/js/migrate_metadata.js --repo <repo>
```

The command is idempotent. It rewrites convertible frontmatter to YAML 2.0,
preserves section evidence (inferring source `role` and adding empty
`unresolved` when absent), migrates embedded manifest provenance objects,
seeds each document's catalog-owned public `description` (from the catalog
`summary`), and
bumps the manifest from `3.5` / `3.4` / `3.3` (or `3.2` / `3.1` / `3.0`) to
`3.6`.

When frontmatter is missing or unparseable, conversion throws, or the result
for a previously written document is still incomplete (scaffold tokens, empty
`sections`, invalid `graph.flow`), migration reports `FAILED`, writes a
best-effort provenance scaffold into the sidecar (keeping the Markdown body),
clears the
audit record, and sets the document status to `in_progress` so the agent can
regenerate concrete provenance and re-ground claims. Planned documents that
only need a scaffold are reported as `REGENERATED` without a status demotion.
`/docforge-revise`, continuing an incomplete run, and
`check_staleness.{py,js} --sync-provenance` invoke the same migration before
their own
work. Lint reports `obsolete schema` and names this command.

### Agent regeneration after `FAILED`

For every `FAILED` path:

1. Treat the document as the next write turn (`in_progress`).
2. Re-ground required claims from the graph and cited sources.
3. Replace every scaffold token with concrete write metadata and heading-matched
   `sections` with valid `git_blob` / `role` values.
4. Set `generated`, run mechanical lint, then an independent audit before
   `complete`.

Do not leave a written document on scaffold tokens or an empty `sections` array.

## Manifest aggregation

The manifest stores the same complete provenance object as the sidecar entry.
`check_staleness.{py,js} --sync-provenance` reads every manifest path,
including root
documents, and replaces only that document's `provenance` value. It never
silently skips malformed or missing provenance.

## Mechanical defects

- `missing provenance`: no sidecar entry, and no frontmatter block or
  `docforge_provenance` key on a pre-migration document.
- `unparseable provenance`: frontmatter YAML/JSON cannot be parsed.
- `legacy provenance`: the provenance object has no `schema`; a document that
  parses cleanly but has no sidecar entry yet reports the same kind, detailed
  as pending migration.
- `obsolete schema`: JSON 1.0 or other pre-2.0 shape; run
  `migrate_metadata.{py,js}` (see
  [`../runtime/manifest/README.md`](../runtime/manifest/README.md)).
- `empty provenance`: a written document has no sections.
- `invalid blob`: `git_blob` is absent or is not 40 lowercase hexadecimal characters.
- `unknown source`: a recorded source path is not a file in the repository.
- `unknown section`: a section id does not match a Markdown heading anchor.

Written documents also fail when any required top-level value is absent,
tokenized, or inconsistent with the manifest. `git_blob_normalized`,
`evidence_range`, and `range_blob` are optional per source; a malformed value
is treated as absent rather than a defect.

## Staleness results

- `FRESH`: every recorded source in scope still matches.
- `PARTIAL` with `STALE`: a source's current blob differs.
- `PARTIAL` with `MISSING`: a recorded source is absent.
- `PARTIAL` with `NO_BLOB`: a source has no valid recorded blob.
- `PARTIAL` with `COSMETIC`: a source's raw blob differs, but its recorded
  `git_blob_normalized` or `range_blob` still matches the current file — the
  cited content is unchanged (whitespace/EOL reflow, or an edit outside the
  cited range). Non-blocking: it does not force re-grounding, and it never
  blocks `check_staleness`'s exit code.
- `UNPARSEABLE`: the document's provenance cannot be parsed during
  synchronization (sidecar entry or pre-migration frontmatter).
- `UNTRACKED`: provenance is missing, empty, or legacy.

Use `--document <id|path>` to limit sync and the report to one manifest entry,
and `--section <id>` to filter sections. Single-document update / refresh
follows the staleness-first path in
[`../workflows/revision.md`](../workflows/revision.md): preserve `FRESH` and
`COSMETIC` sections, re-ground only the blocking `PARTIAL` (`STALE` /
`MISSING` / `NO_BLOB`) ones, and fully rewrite only when the document is
`UNTRACKED` **or its structure / format / content deviates from the current
template** (revise's template-conformance rule). A missing source remains a
review signal because the behavior may have moved; do not delete the
documented claim automatically.
