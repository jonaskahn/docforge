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
# Patterns

<!-- The one docs/agents/ file with real, non-stub content — this has no other home
     in the human-facing tree. -->

## Complexity hotspots

{{table or bullet list: file/module path, why it's a hotspot (size, branching, churn)}}

## Function exemplars

{{per layer, one or two representative functions/files worth reading before writing similar code — path, one-line reason}}

## Recurring imports

{{table: import/module, where it's used, the pattern it signals}}
