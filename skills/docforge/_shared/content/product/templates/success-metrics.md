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
# Success metrics

_Last reviewed: {{YYYY-MM-DD}}_

One entry per feature or epic with a stated success metric — only where instrumented in code or explicitly given by a stakeholder. Never invent a target.


### {{Feature}}

**Metric:** {{what's measured}}
**Instrumented via:** {{the emitted `<event/metric name>` — a stable event/metric name is a public contract, never a private symbol; or the `<module>` by path, or "not instrumented — flag"}}
**Target:** {{only if stated by a stakeholder; omit this line entirely rather than guess}}

<!-- Repeat per feature with a real, checkable metric. Skip features with no
     instrumented or stated metric rather than filling this in speculatively. -->
