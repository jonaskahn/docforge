---
docforge_provenance:
  schema: "2.1"
  doc_id: "<DOC_ID>"
  path: "<DOCUMENT_PATH>"
  generated_at: "<GENERATED_AT>"
  generator:
    name: "docforge"
    version: "2.15.0"
  tier: "<TIER>"
  target_depth: "<TARGET_DEPTH>"
  graph:
    provider: "<GRAPH_PROVIDER>"
    flow: "<FLOW_CAPABILITY>"
  sections: []
---
# Portfolio operations

_Last reviewed: {{YYYY-MM-DD}}_

## Shared operational dependencies

| Dependency | Repos relying on it | Blast radius if it degrades |
|---|---|---|
| {{queue / datastore / on-call rotation}} | {{repos}} | {{portfolio-wide consequence}} |

## Gaps

{{An operational gap that exists because no single member repo owns it.
Link the owning member's own observability.md/deployment.md for local
detail — do not duplicate it here.}}

Shared controls: see [security-posture.md](security-posture.md).
