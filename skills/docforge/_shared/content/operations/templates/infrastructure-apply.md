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
# Infrastructure apply

_Last reviewed: {{YYYY-MM-DD}}_

## Plan/apply safety

**Who may apply:** {{principal or role}}

**Gate between plan and apply:** {{review / approval / CI check}}

```bash
{{plan command}}
{{apply command}}
```

## Drift

**Detection:** {{how drift is detected}}

**Recovery:** {{procedure when actual state diverges from recorded state}}
