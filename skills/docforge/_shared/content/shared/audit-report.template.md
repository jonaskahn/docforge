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
# Audit — {{document path}}

_Audited: {{YYYY-MM-DD}} · Mode: {{subagent | cold-pass}} · Type: {{document type}} · Target depth: {{target depth}}_

## Verdict: {{PASS | FAIL}}

{{One-sentence disposition.}}

## Contract coverage

| Must-present element | Status | Evidence or defect |
|---|---|---|
| {{element}} | {{present | missing | shallow}} | {{artifact/source observation}} |

## Keep-out boundary

{{PASS, or the misplaced/duplicated material.}}

## Grounding spot-check

| Claim | Cited source | Result |
|---|---|---|
| {{claim}} | {{repository-relative source}} | {{matches | unsupported | uncited}} |

## Mechanical checks

{{Lint commands and results.}}

## External tokens

{{Typed token and the external value it represents, or “none.”}}

## Required corrections

{{Ordered corrections, or “none.”}}
