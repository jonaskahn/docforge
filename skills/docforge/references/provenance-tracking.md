# Provenance tracking

This file owns metadata format, validation, and staleness semantics.

## Markdown format

Markdown that supports frontmatter begins at byte one with restricted YAML
provenance 2.0:

```yaml
---
docforge_provenance:
  schema: "2.0"
  doc_id: "architecture_constraints"
  path: "docs/architecture/constraints.md"
  generated_at: "2026-07-27T09:12:44Z"
  generator:
    name: "docforge"
    version: "2.1.0"
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
          role: "code"
      unresolved: []
---
```

The codec in `scripts/provenance_frontmatter.{py,js}` owns emit and parse. It
writes a deterministic YAML subset: 2-space indent, fixed key order, and every
scalar double-quoted. It rejects anchors, aliases, block scalars, multi-document
markers, and non-empty flow collections. `schema` is always `2.0`.

`doc_id` and `path` identify the manifest entry (the PROV entity).
`generated_at` and optional `git_commit` identify the write activity.
`generator.name` and `generator.version` identify the PROV agent / AI
Provenance Protocol generator. Optional `content_hash` is a SHA-256 of the
Markdown body after frontmatter (`sha256:<64 hex>`). Optional `review` records
`mode`, `verdict`, and `report` from the independent audit. `tier` and
`target_depth` carry the content contract. `graph.provider` names the selected
provider and `graph.flow` is `native`, `derived`, or `none`. `graph_snapshot`
is not part of provenance 2.0.

Each section `id` is a Markdown heading anchor. Its sources use repository-
relative file paths, a Git blob hash of the working-tree bytes, and one role:
`code`, `config`, `manifest`, `doc`, `test`, or `history`. `unresolved` lists
typed external tokens intentionally retained in that section.

### Standards mapping

| Docforge field | W3C PROV-DM | AI Provenance Protocol |
|---|---|---|
| `doc_id`, `path` | Entity | content identity |
| `generated_at`, `git_commit` | Activity | generation event |
| `generator` | Agent | `generator` |
| `graph`, `sections[].sources` | used inputs | `inputs` |
| `content_hash` | entity digest | `content_hash` |
| `review` | attribution / derivation note | `review` |

Templates and planned manifest entries use explicit string tokens such as
`<DOC_ID>` and `<GENERATED_AT>` for values unavailable before writing. These
tokens and an empty `sections` array are valid only while a document remains
planned or in progress. Generated, needs-review, and complete documents require
concrete values and at least one section.

Exceptions are `AGENTS.md`, fixed shims such as `CLAUDE.md` and
`CLAUDE.local.md`, and machine JSON configuration. Their provenance is stored
only in the corresponding manifest document entry.

## Migration

JSON provenance 1.0 (`tool_version`, schema `1.0`) is obsolete. Run:

```sh
python scripts/migrate_metadata.py --repo <repo>
```

The command is idempotent. It rewrites convertible frontmatter to YAML 2.0,
migrates embedded manifest provenance objects, and bumps the manifest from
`3.0` to `3.1`. When frontmatter is missing, unparseable, legacy, or otherwise
unconvertible, it regenerates a provenance-2.0 YAML scaffold from the manifest
entry (`doc_id`, `path`, `tier`, `target_depth`, graph tokens) and keeps the
Markdown body. Regenerated documents need a later write pass to refill
`sections` and concrete source blobs. `--revise`, `--resume`, and
`check_staleness --sync-provenance` invoke the same migration before their own
work. Lint reports `obsolete schema` and names this command.

## Manifest aggregation

The manifest stores the same complete provenance object as the document.
`check_staleness --sync-provenance` reads every manifest path, including root
documents, and replaces only that document's `provenance` value. It never
silently skips malformed frontmatter.

## Mechanical defects

- `missing provenance`: no frontmatter block or `docforge_provenance` key.
- `unparseable provenance`: frontmatter YAML/JSON cannot be parsed.
- `legacy provenance`: the provenance object has no `schema`.
- `obsolete schema`: JSON 1.0 or other pre-2.0 shape; run `migrate_metadata`.
- `empty provenance`: a written document has no sections.
- `invalid blob`: `git_blob` is absent or is not 40 lowercase hexadecimal characters.
- `unknown source`: a recorded source path is not a file in the repository.
- `unknown section`: a section id does not match a Markdown heading anchor.

Written documents also fail when any required top-level value is absent,
tokenized, or inconsistent with the manifest.

## Staleness results

- `FRESH`: every recorded source in scope still matches.
- `PARTIAL` with `STALE`: a source's current blob differs.
- `PARTIAL` with `MISSING`: a recorded source is absent.
- `PARTIAL` with `NO_BLOB`: a source has no valid recorded blob.
- `UNPARSEABLE`: document frontmatter cannot be parsed during synchronization.
- `UNTRACKED`: provenance is missing, empty, or legacy.

Use `--section <id>` to filter. A missing source remains a review signal because
the behavior may have moved; do not delete the documented claim automatically.
