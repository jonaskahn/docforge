---
docforge_provenance:
  schema: "2.0"
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
# State management

_Last reviewed: {{YYYY-MM-DD}}_

## {{State domain}}

**Owner:** {{who mutates this}}

**Read by:** {{consumers}}

**On bad transition:** {{failure/recovery behavior}}

Render lifecycle: see [rendering.md](rendering.md).
