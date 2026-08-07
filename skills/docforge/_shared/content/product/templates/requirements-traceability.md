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
# Requirements traceability

_Last reviewed: {{YYYY-MM-DD}}_

Maps requirement → implementation → verification. Open this file when a stakeholder asks whether the system actually does what was asked for.


### Traceability table

| Requirement (stakeholder's own wording, if available) | Business rule(s) implementing it | Code location | Test coverage | Status |
|---|---|---|---|---|
| {{requirement text, or `<ORIGINAL_REQ_WORDING>` token if the stakeholder's own wording isn't recoverable}} | [{{rule name}}](./business-rules.md#{{rule-slug}}) | {{path/to/module}} | {{test file/name, or "none — flag"}} | {{implemented / partial / not started}} |

<!-- One row per requirement. The rule, its code location and its tests are all
     derivable — write them in full. Never invent stakeholder wording that isn't
     recoverable from a connected source; leave only that value as the
     <ORIGINAL_REQ_WORDING> typed token. -->
