---
docforge_provenance:
  schema: "2.0"
  doc_id: "<DOC_ID>"
  path: "<DOCUMENT_PATH>"
  generated_at: "<GENERATED_AT>"
  generator:
    name: "docforge"
    version: "2.8.0"
  tier: "<TIER>"
  target_depth: "<TARGET_DEPTH>"
  graph:
    provider: "<GRAPH_PROVIDER>"
    flow: "<FLOW_CAPABILITY>"
  sections: []
---
# Data quality

_Last reviewed: {{YYYY-MM-DD}}_

<!--
Optional — dataset relationships: if a relationship between the datasets
below is durable and evidenced (not inferred), add one `mermaid erDiagram`
block here, at most 8 entities, per ../../../references/illustration.md.
Omit this comment and add nothing otherwise.
-->

## {{Dataset name}}

**Producer:** {{system or job that creates this dataset}}

**Transformation boundary:** {{where raw input becomes this dataset — job, service, or path}}

**Data contract:** {{linked contract file or schema definition, or "none"}}

**Schema owner:** {{team or role accountable for schema changes}}

**On failure:** {{runbook or recovery handoff — link or role}}

{{Repeat this block per governed dataset.}}

## Quality checks

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
