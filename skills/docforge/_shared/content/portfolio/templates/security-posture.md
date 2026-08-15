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
# Security posture

_Last reviewed: {{YYYY-MM-DD}}_

## Shared controls

| Control | Repos covered | Repos not covered |
|---|---|---|
| {{control}} | {{repos}} | {{repos, or "none"}} |

## Shared dependencies and coupling

{{One entry per shared dependency: what it is, which repos rely on it, and
the blast radius across the portfolio if it fails.}}

## Gaps

{{A gap that exists because no single member repo owns it. Link to the
owning member's own threat-model.md or equivalent for local detail — do
not duplicate it here.}}
