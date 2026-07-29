---
docforge_provenance:
  schema: "2.0"
  doc_id: "<DOC_ID>"
  path: "<DOCUMENT_PATH>"
  generated_at: "<GENERATED_AT>"
  generator:
    name: "docforge"
    version: "2.1.0"
  tier: "<TIER>"
  target_depth: "<TARGET_DEPTH>"
  graph:
    provider: "<GRAPH_PROVIDER>"
    flow: "<FLOW_CAPABILITY>"
  sections: []
---
# Flow index

This index lists every evidence-backed flow candidate. **Main** rows are
prioritized for deep-dive documentation; **deferred** rows remain discoverable
without creating placeholder documents.

| Status | Flow | Trigger | Entry point | Area | Confidence | Reach |
|---|---|---|---|---|---|---|
| {{main / deferred / documented / skipped}} | {{flow}} | {{trigger kind}} | `{{normalized entry signature}}` | {{area}} | {{confirmed / candidate}} | {{steps / boundaries}} |

The machine-readable source of truth is `.docforge/flow-index.json`.
