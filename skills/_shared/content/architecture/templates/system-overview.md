---
docforge_provenance:
  schema: "2.0"
  doc_id: "<DOC_ID>"
  path: "<DOCUMENT_PATH>"
  generated_at: "<GENERATED_AT>"
  generator:
    name: "docforge"
    version: "2.5.0"
  tier: "<TIER>"
  target_depth: "<TARGET_DEPTH>"
  graph:
    provider: "<GRAPH_PROVIDER>"
    flow: "<FLOW_CAPABILITY>"
  sections: []
---
# System overview

_Last reviewed: {{YYYY-MM-DD}}_

{{One paragraph: the handful of major capabilities and how they hang together.}}

```mermaid
flowchart LR
  User["{{actor}}"] --> App["{{this system}}"]
  App --> Ext["{{boundary system}}"]
```

## Primary end-to-end path

```mermaid
sequenceDiagram
  participant Actor as {{actor}}
  participant Sys as {{subsystem}}
  participant Ext as {{external}}
  Actor->>Sys: {{request}}
  Sys->>Ext: {{call}}
  Ext-->>Sys: {{response}}
  Sys-->>Actor: {{outcome}}
```

## Feature → owning flow → subsystem

| Capability | Owning flow | Implementing subsystem |
|---|---|---|
| {{capability}} | [{{flow}}](../flows/README.md) | {{subsystem}} |

Link out to [`docs/flows/README.md`](../flows/README.md) for the full matrix;
do not duplicate its rows.
