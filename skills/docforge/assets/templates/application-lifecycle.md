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
# Application lifecycle

_Last reviewed: {{YYYY-MM-DD}}_

```mermaid
stateDiagram-v2
  [*] --> Launch
  Launch --> Active
  Active --> Background
  Background --> Active
  Background --> Terminated
  Terminated --> [*]
```

## {{State}}

**Trigger:** {{what enters this state}}

**Must do before leaving:** {{cleanup/save}}

**Restoration on relaunch:** {{behavior}}

**On kill mid-transition:** {{failure boundary}}
