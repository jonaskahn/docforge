---
docforge_provenance:
  schema: "2.1"
  doc_id: "<DOC_ID>"
  path: "<DOCUMENT_PATH>"
  generated_at: "<GENERATED_AT>"
  generator:
    name: "docforge"
    version: "2.17.0"
  tier: "<TIER>"
  target_depth: "<TARGET_DEPTH>"
  graph:
    provider: "<GRAPH_PROVIDER>"
    flow: "<FLOW_CAPABILITY>"
  sections: []
---
# Output and exit codes

_Last reviewed: {{YYYY-MM-DD}}_

## Exit codes

| Code | Meaning | Stable to script against |
|---|---|---|
| {{0}} | {{success}} | {{yes}} |
| {{N}} | {{meaning}} | {{yes/no}} |

## Streams

**stdout:** {{machine-parseable output / human output}}

**stderr:** {{diagnostics}}

**Format stability:** {{schema-versioned? can fields disappear in a minor release?}}

## Example output

```{{format}}
{{captured, real output}}
```
