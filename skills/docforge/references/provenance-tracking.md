# Provenance tracking

This file owns metadata format and staleness semantics.

## Markdown format

Markdown that supports frontmatter begins at byte one with a JSON value inside
frontmatter delimiters:

```text
---
{"docforge_provenance":{"sections":[{"id":"configuration","sources":[{"path":"src/config.ts","git_blob":"<GIT_BLOB_SHA1>"}]}]}}
---
# Configuration
```

JSON is a strict YAML subset and is parsed with standard-library JSON in both
runtimes. `git_blob` is the Git blob hash of working-tree bytes, not a commit
hash. Record repository-relative files, never a directory or “the codebase.”

Exceptions are `AGENTS.md`, fixed shims such as `CLAUDE.md` and
`CLAUDE.local.md`, and machine JSON configuration. Their provenance is stored
only in the corresponding manifest document entry.

## Manifest aggregation

Each document has:

```json
{
  "provenance_mode": "sections",
  "provenance": {
    "sections": [
      {
        "id": "configuration",
        "sources": [
          {"path": "src/config.ts", "git_blob": "<GIT_BLOB_SHA1>"}
        ]
      }
    ]
  }
}
```

`check_staleness --sync-provenance` reads every manifest path, including root
documents, and replaces only `provenance.sections`. It preserves the document
id, type, path, selection, status, requirements, audit, and all plan metadata.

## Results

- `FRESH`: every recorded source in scope still matches.
- `PARTIAL`: a source for one section changed or disappeared. Rewrite only that
  section unless the document structure itself changed.
- `UNTRACKED`: a written document has no provenance. Re-ground it before
  adopting it into incremental maintenance.

Use `--section <id>` to filter. A missing source remains a review signal because
the behavior may have moved; do not delete the documented claim automatically.
