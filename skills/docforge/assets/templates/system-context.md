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
# System context

_Last reviewed: {{YYYY-MM-DD}}_

```mermaid
flowchart LR
  Member1["{{member repo}}"] --> Shared["{{shared service}}"]
  Member2["{{member repo}}"] --> Shared
  Shared --> External["{{external system}}"]
```

{{One paragraph: what the portfolio borders and how members relate.}}

## Cross-repo flows

| Trigger | Repos involved | Outcome | Owning flow |
|---|---|---|---|
| {{trigger}} | {{repos}} | {{outcome}} | {{link to owning repo's flow doc}} |
