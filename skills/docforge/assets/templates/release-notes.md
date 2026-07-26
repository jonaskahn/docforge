# Release notes

_Last generated: {{YYYY-MM-DD}}_

User-facing changelog, distinct from the root `CHANGELOG.md` (commit-level, technical). Built by walking merge commits since the last entry and translating each into user impact. Skip purely internal changes — refactors, dependency bumps, test additions — a reader who sees internal noise here stops reading.

---
docforge_provenance:
  doc: docs/product/product-owner/release-notes.md
  generated_at: {{ISO-8601 timestamp}}
  sections:
    - id: {{version-slug, e.g. v2-4-0}}
      sources:
        - path: {{src/module/file.ext}}
          git_blob: {{git hash-object output}}
---

## {{vX.Y.Z}} — {{YYYY-MM-DD}}

- {{User-facing change, in plain language}} ({{linked feature in feature-catalog.md, if applicable}})
- {{...}}

<!-- One version heading per release. Add a `sections` entry per version so
     a later re-check knows which source changes already made it into notes. -->
