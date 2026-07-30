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
# Publishing

_Last reviewed: {{YYYY-MM-DD}}_

**Version source:** {{file / tag / generator}}

1. Build — `{{command}}` — verify: {{signal}}
2. Sign — {{mechanism}}
3. Publish to {{registry/channel}} — `{{command}}` — verify: {{signal}}

## Rollback / deprecate

1. {{step}}

Released changes: record in [changelog.md](changelog.md).
