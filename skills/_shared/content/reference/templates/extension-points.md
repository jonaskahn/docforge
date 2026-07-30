---
docforge_provenance:
  schema: "2.0"
  doc_id: "<DOC_ID>"
  path: "<DOCUMENT_PATH>"
  generated_at: "<GENERATED_AT>"
  generator:
    name: "docforge"
    version: "2.6.0"
  tier: "<TIER>"
  target_depth: "<TARGET_DEPTH>"
  graph:
    provider: "<GRAPH_PROVIDER>"
    flow: "<FLOW_CAPABILITY>"
  sections: []
---
# Extension points

_Last reviewed: {{YYYY-MM-DD}}_

| Extension point | Lets an integrator do | Permission scope | Sandbox boundary |
|---|---|---|---|
| {{point}} | {{capability}} | {{scope}} | {{what it cannot reach}} |

**On extension crash:** {{failure behavior}}

Host contract: see [host-integration.md](host-integration.md).
