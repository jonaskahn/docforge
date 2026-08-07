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
# Release guide

_Last reviewed: {{YYYY-MM-DD}}_

## Prerequisites

{{What must be true before starting a release — branch state, required checks green, access.}}

## Version

**Scheme:** {{SemVer or equivalent}}. Major: {{trigger}} · Minor: {{trigger}} · Patch: {{trigger}}

## Build

1. `{{command}}` — verify: {{success signal}}

## Verification

**Required gate:** {{evidenced check or approval}} — owned by {{responsible role}}.

1. `{{command}}` — verify: {{success signal}}

## Publication

1. `{{command}}` — verify: {{success signal}}

## Rollback

**Trigger:** {{release-health signal that forces a rollback, e.g. an error-rate threshold, and who escalates it}}.

1. {{step}} — verify: {{success signal}}

Released changes: record in [changelog.md](changelog.md).
