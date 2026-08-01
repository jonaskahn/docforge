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
# Flows (agent view)

<!-- Brief stub — entry points and triggers only. Full steps live in docs/flows/,
      sourced from repository evidence. Gated the same as docs/flows/ — see
     runtime/cli/python/precheck_graph.py --need flow. -->

{{one bullet per domain: `- {{domain}}: entry at {{trigger/route}} → [flows/{{flow}}.md](../flows/{{flow}}.md)`}}
