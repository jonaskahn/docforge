---
docforge_provenance:
  schema: "2.0"
  doc_id: "<DOC_ID>"
  path: "<DOCUMENT_PATH>"
  generated_at: "<GENERATED_AT>"
  generator:
    name: "docforge"
    version: "2.6.0"
  tier: "<TIER>"
  target_depth: "<TARGET_DEPTH>"
  graph:
    provider: "<GRAPH_PROVIDER>"
    flow: "<FLOW_CAPABILITY>"
  sections: []
---
# Observability

_Last reviewed: {{YYYY-MM-DD}}_

## Signals

| Signal | Source | Visible in | Owner | Alert intent |
|---|---|---|---|---|
| Latency | {{source}} | {{dashboard/log/trace}} | {{owner}} | {{page / log-only}} |
| Traffic | {{source}} | {{...}} | {{owner}} | {{...}} |
| Errors | {{source}} | {{...}} | {{owner}} | {{...}} |
| Saturation | {{source}} | {{...}} | {{owner}} | {{...}} |

## Correlation

{{How a reader moves from an alert to the request or trace that caused it.}}

## Blind spots

{{What this system cannot currently observe.}}
