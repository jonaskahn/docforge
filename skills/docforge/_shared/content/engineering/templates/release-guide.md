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
# Release guide

_Last reviewed: {{YYYY-MM-DD}}_

## Prerequisites

{{What must be true before starting a release.}}

## Version

**Scheme:** {{SemVer or equivalent}}. Major: {{trigger}} · Minor: {{trigger}} · Patch: {{trigger}}

## Release

1. `{{command}}` — verify: {{success signal}}
2. `{{command}}` — verify: {{success signal}}

## Rollback

1. {{step}}

Released changes: record in [changelog.md](changelog.md).
