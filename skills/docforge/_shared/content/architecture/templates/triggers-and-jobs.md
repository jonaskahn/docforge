---
docforge_provenance:
  schema: "2.0"
  doc_id: "<DOC_ID>"
  path: "<DOCUMENT_PATH>"
  generated_at: "<GENERATED_AT>"
  generator:
    name: "docforge"
    version: "2.7.0"
  tier: "<TIER>"
  target_depth: "<TARGET_DEPTH>"
  graph:
    provider: "<GRAPH_PROVIDER>"
    flow: "<FLOW_CAPABILITY>"
  sections: []
---
# Triggers and jobs

_Last reviewed: {{YYYY-MM-DD}}_

## {{Job name}}

**Trigger:** {{schedule / event / manual}}

**Payload:** {{shape}}

**Concurrency:** {{overlapping instances allowed? what happens if so}}

**Downstream effect:** {{what happens once it completes}}

**Owner:** {{team or role}}

Reliability detail (retry, idempotency, dead-letter): see
[job-reliability.md](job-reliability.md).
