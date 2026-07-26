# Feature catalog

_Last generated: {{YYYY-MM-DD}}_

Reframes `../capabilities.md` around value and status for planning conversations. Do not restate capability descriptions here — link to them.

---
docforge_provenance:
  doc: docs/product/product-owner/feature-catalog.md
  generated_at: {{ISO-8601 timestamp}}
  sections:
    - id: {{feature-slug}}
      sources:
        - path: {{src/module/file.ext}}
          git_blob: {{git hash-object output}}
---

### Feature: {{name}}

**Value:** {{the business or user outcome, one sentence}}
**Status:** {{shipped (vX.Y) / in progress / planned / deprecated (sunset date)}}
**Owns:** {{flow(s) implementing it}} — see [process-flows.md](../business-analyst/process-flows.md#{{flow-slug}}) or [architecture overview](../../architecture/overview.md)
**Depends on:** {{other features or external services this needs}}

<!-- Repeat per feature. One `sections` entry per feature. -->
