---
docforge_provenance:
  schema: "2.1"
  doc_id: "<DOC_ID>"
  path: "<DOCUMENT_PATH>"
  generated_at: "<GENERATED_AT>"
  generator:
    name: "docforge"
    version: "2.8.0"
  tier: "<TIER>"
  target_depth: "<TARGET_DEPTH>"
  graph:
    provider: "<GRAPH_PROVIDER>"
    flow: "<FLOW_CAPABILITY>"
  sections: []
---
# Flows

{{One or two sentences introducing the flow layer: what a "flow" is in this
repository, how flows were discovered, and how this index relates to the flow
documents that deep-dive the main candidates.}}

## How to read this index

This index lists every evidence-backed flow candidate. **Main** priority
**standalone** rows get deep-dive documentation; **member** rows are composed
into a parent; **index_only** / deferred rows remain discoverable without stub
files.

## {{family or Ungrouped}}

<!-- docforge-children:start -->
| Status | Role | Flow | Trigger | Entry point | Area | Confidence | Reach |
|---|---|---|---|---|---|---|---|
| {{main / deferred / placeholder / documented / skipped}} | {{standalone / member / index_only}} | {{flow}} | {{trigger kind}} | `{{normalized entry signature}}` | {{area}} | {{confirmed / candidate}} | {{steps / boundaries}} |
<!-- docforge-children:end -->

The machine-readable source of truth is `.docforge/flow-index.json`.
