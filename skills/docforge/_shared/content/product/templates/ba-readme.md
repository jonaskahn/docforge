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
# Business Analyst documentation

_Last generated: {{YYYY-MM-DD}}_

Documentation for {{repo_name}} written for business analysts: exact business rules, process flows as executed, and requirements traceability. If you're an engineer looking for architecture, see `../../architecture/`. If you're a product owner, see `../product-owner/`.

| File | Answers |
|---|---|
| [business-rules.md](./business-rules.md) | What exactly does the system enforce, and where? |
| [process-flows.md](./process-flows.md) | What are the business-level steps, in order, and where do they branch? |
| [requirements-traceability.md](./requirements-traceability.md) | Did we build what was actually asked for? |

If Product Owner documentation is also needed, see `../product-owner/`.
