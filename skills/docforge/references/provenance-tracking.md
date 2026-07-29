# Provenance tracking

This file owns metadata format, validation, and staleness semantics.

## Markdown format

Markdown that supports frontmatter begins at byte one with multiline,
pretty-printed JSON:

```text
---
{
  "docforge_provenance": {
    "schema": "1.0",
    "doc_id": "architecture_constraints",
    "path": "docs/architecture/constraints.md",
    "generated_at": "2026-07-27T09:12:44Z",
    "tool_version": "2.0.0",
    "tier": "diligence",
    "target_depth": "deep-dive",
    "graph": {
      "provider": "gitnexus",
      "flow": "native"
    },
    "git_commit": "9f1c0aa4e2b7d3915c6f0b8ad24e7c31b5a0e6d2",
    "sections": [
      {
        "id": "ceilings",
        "sources": [
          {
            "path": "src/server.js",
            "git_blob": "3b18e512dba79e4c8300dd08aeb37f8e728b8dad",
            "role": "code"
          }
        ],
        "unresolved": []
      }
    ]
  }
}
---
```

JSON is parsed with standard-library JSON in both runtimes. `schema` is always
`1.0`. `doc_id` and `path` identify the manifest entry; `generated_at` and
`tool_version` identify the write; `tier` and `target_depth` carry its content
contract. `graph.provider` names the selected provider and `graph.flow` is
`native`, `derived`, or `none`. The optional `git_commit` is the repository
commit at write time. `graph_snapshot` is not part of provenance v1.

Each section `id` is a Markdown heading anchor. Its sources use repository-
relative file paths, a Git blob hash of the working-tree bytes, and one role:
`code`, `config`, `manifest`, `doc`, `test`, or `history`. `unresolved` lists
typed external tokens intentionally retained in that section.

Templates and planned manifest entries use explicit JSON string tokens such as
`<DOC_ID>` and `<GENERATED_AT>` for values unavailable before writing. These
tokens and an empty `sections` array are valid only while a document remains
planned or in progress. Generated, needs-review, and complete documents require
concrete values and at least one section.

Exceptions are `AGENTS.md`, fixed shims such as `CLAUDE.md` and
`CLAUDE.local.md`, and machine JSON configuration. Their provenance is stored
only in the corresponding manifest document entry.

## Manifest aggregation

The manifest stores the same complete provenance object as the document.
`check_staleness --sync-provenance` reads every manifest path, including root
documents, and replaces only that document's `provenance` value. It never
silently skips malformed frontmatter.

## Mechanical defects

- `missing provenance`: no frontmatter block or `docforge_provenance` key.
- `unparseable provenance`: frontmatter JSON cannot be parsed.
- `legacy provenance`: the provenance object has no `schema`.
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
