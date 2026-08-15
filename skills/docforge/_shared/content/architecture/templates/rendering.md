---
docforge_provenance:
  schema: "2.1"
  doc_id: "<DOC_ID>"
  path: "<DOCUMENT_PATH>"
  generated_at: "<GENERATED_AT>"
  generator:
    name: "docforge"
    version: "2.16.0"
  tier: "<TIER>"
  target_depth: "<TARGET_DEPTH>"
  graph:
    provider: "<GRAPH_PROVIDER>"
    flow: "<FLOW_CAPABILITY>"
  sections: []
---
# Rendering

_Last reviewed: {{YYYY-MM-DD}}_

**Renders where:** {{server / client / server-then-client handoff}}

```mermaid
stateDiagram-v2
  [*] --> Mount
  Mount --> Update
  Update --> Update
  Update --> Unmount
  Unmount --> [*]
```

_Repeat per stage — Mount, Update, Unmount above._

## {{Lifecycle stage}}

**Trigger:** {{what causes this transition}}

**Behavior:** {{what happens}}

**Loading/error presentation:** {{what the user sees while pending, and on
a render-boundary failure}}

**On render failure:** {{recovery — retry, fallback UI, error boundary
escalation}}

State ownership: see [state.md](state.md). Component catalog: see
[ui-components.md](ui-components.md).
