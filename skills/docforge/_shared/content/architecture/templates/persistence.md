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
# Persistence

_Last reviewed: {{YYYY-MM-DD}}_

```mermaid
erDiagram
  ENTITY1 ||--o{ ENTITY2 : "{{relationship}}"
```

_Repeat per entity — the ones material to the storage model, not every table._

## {{Entity}}

**Storage:** {{table/collection}} · **Key:** {{strategy}}

**Denormalization:** {{if any, and why}}

## Migrations

**Mechanism:** {{tool}} · **Versioning:** {{scheme}} · **Reversible:** {{yes/no}}

## Transaction and consistency boundary

{{What's atomic together; consistency model where it isn't (eventual /
read-your-writes / none).}}

## Failure recovery

{{What happens to a write in flight during a crash — one paragraph per entity
whose behavior differs, or one shared statement if all entities behave alike.}}
