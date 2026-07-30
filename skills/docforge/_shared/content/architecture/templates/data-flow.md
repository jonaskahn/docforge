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
# Data flow

_Last reviewed: {{YYYY-MM-DD}}_

## {{Lineage name, e.g. Order event pipeline}}

```mermaid
flowchart LR
  Producer["{{producer}}"] --> Transform1["{{transformation}}"]
  Transform1 --> Transform2["{{transformation}}"]
  Transform2 --> Consumer["{{consumer}}"]
```

{{One paragraph: what crosses each arrow and why it matters.}}

### Producer: {{name}}

{{What it emits, and the contract it guarantees about the output.}}

### {{Transformation name}}

**Guarantees:** {{schema / ordering / completeness the next stage can rely on.}}

Schema owned by: [data-types.md](data-types.md#{{anchor}})

### Consumer: {{name}}

{{What it expects, and what it does with the data.}}

## Failure and recovery

{{What happens to in-flight data on a stage failure — replay, drop, or
dead-letter — for this lineage.}}
