---
docforge_provenance:
  schema: "2.0"
  doc_id: "<DOC_ID>"
  path: "<DOCUMENT_PATH>"
  generated_at: "<GENERATED_AT>"
  generator:
    name: "docforge"
    version: "2.6.1"
  tier: "<TIER>"
  target_depth: "<TARGET_DEPTH>"
  graph:
    provider: "<GRAPH_PROVIDER>"
    flow: "<FLOW_CAPABILITY>"
  sections: []
---
# Infrastructure state

_Last reviewed: {{YYYY-MM-DD}}_

**State location:** {{where state lives}}

**Locking mechanism:** {{how concurrent writers are prevented}}

**Owner:** {{who owns this state}}

## Drift

**Detection:** {{mechanism}}

**Recovery:** {{procedure}}

Apply safety: see [infrastructure-apply.md](infrastructure-apply.md).
