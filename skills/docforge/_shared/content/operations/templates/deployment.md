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
# Deployment

_Last reviewed: {{YYYY-MM-DD}}_

## {{Environment, e.g. Production}}

**Artifact source:** {{where the deployable artifact comes from}}

**Rollout strategy:** {{blue-green / canary / rolling}}

1. {{step}} — verify: {{observable success signal}}
2. {{step}} — verify: {{observable success signal}}

## Rollback

1. {{step}}

```bash
{{verification command}}
```

Environment differences: see [environments.md](environments.md). Incident
recovery: see [disaster-recovery.md](disaster-recovery.md).
