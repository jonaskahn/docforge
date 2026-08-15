---
docforge_provenance:
  schema: "2.1"
  doc_id: "<DOC_ID>"
  path: "<DOCUMENT_PATH>"
  generated_at: "<GENERATED_AT>"
  generator:
    name: "docforge"
    version: "2.17.0"
  tier: "<TIER>"
  target_depth: "<TARGET_DEPTH>"
  graph:
    provider: "<GRAPH_PROVIDER>"
    flow: "<FLOW_CAPABILITY>"
  sections: []
---
# Gameplay systems

_Last reviewed: {{YYYY-MM-DD}}_

_Repeat per system — the `##` block below._

## {{System, e.g. Combat}}

**Owns:** {{responsibility}} · **Does not own:** {{boundary}}

**Update order:** {{where this system falls in the event/update sequence
relative to others it depends on}}

**Save-state contract:** {{what persists across sessions, and how}}

**On incompatible save:** {{behavior when a save predates this system's
current data shape — migrate, reset, or reject}}

Scenes and assets: see [assets-and-scenes.md](assets-and-scenes.md).
