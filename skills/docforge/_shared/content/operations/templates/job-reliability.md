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
# Job reliability

_Last reviewed: {{YYYY-MM-DD}}_

| Job class | Retry | Idempotency | Timeout | Backpressure | Dead-letter | Replay |
|---|---|---|---|---|---|---|
| {{class}} | {{count + backoff}} | {{mechanism or "none"}} | {{value + on-timeout behavior}} | {{behavior}} | {{destination}} | {{procedure}} |

Job identity and triggers: see
[triggers-and-jobs.md](triggers-and-jobs.md).
