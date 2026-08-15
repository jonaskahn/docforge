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
# Threat register

This register expands the bounded model in [threat-model.md](threat-model.md).

| ID | Origin -> destination | Interaction | STRIDE | Score | Disposition / control | Owner | Residual uncertainty | Evidence |
|---|---|---|---|---|---|---|---|---|
| TR-001 | {{origin -> destination}} | {{active verb + protocol}} | {{category}} | {{LxI or unscored}} | {{one response + testable control}} | {{established owner or unknown}} | {{what remains}} | {{safe source anchor}} |
