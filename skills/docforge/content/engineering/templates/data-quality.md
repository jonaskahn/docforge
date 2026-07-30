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
# Data quality

_Last reviewed: {{YYYY-MM-DD}}_

| Dimension | Check | Enforcement point | On failure | Evidence |
|---|---|---|---|---|
| Accuracy | {{check}} | {{ingestion / transform / scheduled audit}} | {{reject / quarantine / alert-only / auto-correct}} | {{full / sampled}} |
| Completeness | {{check}} | {{point}} | {{behavior}} | {{full / sampled}} |
| Timeliness | {{check}} | {{point}} | {{behavior}} | {{full / sampled}} |
| Validity | {{check}} | {{point}} | {{behavior}} | {{full / sampled}} |
| Uniqueness | {{check}} | {{point}} | {{behavior}} | {{full / sampled}} |
| Consistency | {{check}} | {{point}} | {{behavior}} | {{full / sampled}} |

{{Drop any dimension with no evidenced check rather than filling the row
with an aspiration.}}
