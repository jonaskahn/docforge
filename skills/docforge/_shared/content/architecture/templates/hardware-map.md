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
# Hardware map

_Last reviewed: {{YYYY-MM-DD}}_

| Board / peripheral | Revision | Protocol | Memory / power budget | On fault or absence | Source |
|---|---|---|---|---|---|
| {{name (interface role, e.g. sensor/actuator/comms)}} | {{stable revision id}} | {{protocol}} | {{unit-qualified budget}} | {{failure mode}} | {{datasheet/schematic reference, or `unknown`}} |

Firmware states: see [firmware-lifecycle.md](firmware-lifecycle.md).
