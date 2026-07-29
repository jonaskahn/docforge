---
{
  "docforge_provenance": {
    "schema": "1.0",
    "doc_id": "<DOC_ID>",
    "path": "<DOCUMENT_PATH>",
    "generated_at": "<GENERATED_AT>",
    "tool_version": "2.0.0",
    "tier": "<TIER>",
    "target_depth": "<TARGET_DEPTH>",
    "graph": {
      "provider": "<GRAPH_PROVIDER>",
      "flow": "<FLOW_CAPABILITY>"
    },
    "sections": []
  }
}
---
# Flows (agent view)

<!-- Brief stub — entry points and triggers only. Full steps live in docs/flows/,
     sourced from the selected flow graph. Gated the same as docs/flows/ — see
     scripts/precheck_graph.py --need flow. -->

{{one bullet per domain: `- {{domain}}: entry at {{trigger/route}} → [flows/{{flow}}.md](../flows/{{flow}}.md)`}}
