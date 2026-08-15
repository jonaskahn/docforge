---
docforge_provenance:
  schema: "2.1"
  doc_id: "<DOC_ID>"
  path: "<DOCUMENT_PATH>"
  generated_at: "<GENERATED_AT>"
  generator:
    name: "docforge"
    version: "2.17.0"
  tier: "<TIER>"
  target_depth: "<TARGET_DEPTH>"
  graph:
    provider: "<GRAPH_PROVIDER>"
    flow: "<FLOW_CAPABILITY>"
  sections: []
---
# Feature catalog

_Last reviewed: {{YYYY-MM-DD}}_

Reframes `../capabilities.md` around value and status for planning conversations. Do not restate capability descriptions here — link to them.


### Feature: {{name}}

**Value:** {{the business or user outcome, one sentence}}
**Status:** {{shipped (vX.Y) / in progress / planned / deprecated (sunset date)}}
**Owns:** {{flow(s) implementing it}} — see [process-flows.md](../business-analyst/process-flows.md#{{flow-slug}}) or [architecture overview](../../architecture/high-level.md)
**Depends on:** {{other features or external services this needs}}

<!-- Repeat per feature. One `sections` entry per feature. -->
