---
docforge_provenance:
  schema: "2.1"
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
# Disaster recovery

_Last reviewed: {{YYYY-MM-DD}}_

## {{Scenario, e.g. Primary datastore loss}}

**RTO:** {{time}} · **RPO:** {{data-loss window}}

**Stop conditions:** {{state that means "escalate" vs "keep going"}}

1. {{recovery step, dependency order}}
2. {{step}}

```bash
{{verification command}}
```

**Data-loss boundary:** {{exact point in time data recovers to}}
