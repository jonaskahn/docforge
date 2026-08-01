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
# Technical debt

_Last reviewed: {{YYYY-MM-DD}}_

Known shortcuts and deferred work, recorded honestly. Debt hidden reads as evasion under
scrutiny; debt named with a remediation path reads as competence. Describe the shortcut and
its cost in behavioural terms — do not paste the offending code.

## Register

| Item | What was deferred / shortcut taken | Why | Cost it imposes | Remediation | Tracking |
|---|---|---|---|---|---|
| {{name}} | {{the shortcut, described}} | {{deadline, unknown, dependency}} | {{who pays, how, when}} | {{what fixing it takes}} | {{tracker ref}} |

## Notes

{{Optional: debt that is deliberate and acceptable for now, distinguished from debt that
should be paid down soon. Say which is which — an undated, unranked list is ignored.}}

_Distinct from [constraints.md](constraints.md) (hard limits by design) and
[../reference/limitations.md](../reference/limitations.md) (feature gaps a user hits).
Cross-link; do not duplicate._
