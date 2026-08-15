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
# API versioning

_Last reviewed: {{YYYY-MM-DD}}_

## Compatibility promise

{{One paragraph: what changes without a version bump (additive fields, new
optional parameters) and what forces one (removed fields, changed types,
changed error semantics).}}

## How to pin a version

{{Header, path segment, or account default — the exact mechanism a caller
uses.}}

## Current version

**Version:** {{version}} · **Released:** {{YYYY-MM-DD}}

## Deprecations

| Feature | Deprecated in | Removed in | Replacement |
|---|---|---|---|
| {{feature}} | {{version}} | {{version or "not yet scheduled"}} | {{replacement}} |

Operation-level detail lives in [api-reference.md](api-reference.md); this
page owns the compatibility promise, not the surface.
