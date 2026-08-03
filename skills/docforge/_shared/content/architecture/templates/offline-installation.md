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
# Offline and installation

_Last reviewed: {{YYYY-MM-DD}}_

**Installability criteria:** {{what makes this installable}}

```mermaid
stateDiagram-v2
  [*] --> Cached
  Cached --> Updating
  Updating --> Cached
  Cached --> Stale
  Stale --> Updating
```

**Cache contents:** {{what's cached}}

**Update trigger:** {{when the cache refreshes — periodic, on-deploy, on-demand}}

**Invalidation:** {{how stale cache is detected/cleared}}

## Offline boundary

_One row per feature; leave a cell blank where a category doesn't apply._

| Works offline | Degrades | Fails |
|---|---|---|
| {{feature}} | {{feature}} | {{feature}} |

**On reconnect:** {{recovery behavior}}
