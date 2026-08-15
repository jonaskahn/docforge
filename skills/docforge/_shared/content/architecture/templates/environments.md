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
# Environments

_Last reviewed: {{YYYY-MM-DD}}_

| Dimension | {{Dev}} | {{Staging}} | {{Production}} |
|---|---|---|---|
| Configuration | {{value/source}} | {{...}} | {{...}} |
| Scale | {{...}} | {{...}} | {{...}} |
| Data realism | {{...}} | {{...}} | {{...}} |
| External services | {{stub/real}} | {{...}} | {{...}} |
| Config owner | {{team/system}} | {{...}} | {{...}} |

Configuration values themselves live in
[reference/configuration.md](../reference/configuration.md) — this table states
who owns each environment's settings, not the values.

## Promotion boundary

{{What must be true before a change moves to the next environment, and who
owns that gate.}}
