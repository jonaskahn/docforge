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
# Host integration

_Last reviewed: {{YYYY-MM-DD}}_

**Host:** {{what this extends}}

**Activation events:** {{what triggers activation}}

**Compatibility range:** {{host versions supported}}

**Permission scope:** {{what an integration can access in the host — link to
[security/platform-permissions.md](security/platform-permissions.md) rather
than repeating rationale}}

**Sandbox boundary:** {{what an integration cannot reach, enforced by the host}}

**On incompatible host:** {{behavior}}

**On extension failure:** {{host-side containment — does the host survive, does
it disable the extension, does it surface an error}}

Contribution points: see [extension-points.md](extension-points.md).
