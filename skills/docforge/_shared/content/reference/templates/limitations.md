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
# Limitations and known issues

_Last reviewed: {{YYYY-MM-DD}}_

Read this before building on {{repo_name}}.

## Known limitations

Design constraints and deliberate trade-offs — the shape of the system, not defects.

| Area | Limitation | Impact | Workaround | Tracking |
|---|---|---|---|---|
| {{area}} | {{what it cannot do}} | {{who is affected, how}} | {{if any}} | {{ref}} |

## Known issues

Defects under investigation.

| Issue | Symptom | Affected versions | Status |
|---|---|---|---|

## Not supported

Things a reasonable person expects and will not find.

- {{X}} is not supported. {{Planned / not planned, and why.}}

## Scale and performance envelope

| Dimension | Tested limit | Notes |
|---|---|---|
| {{requests/sec}} | {{value}} | {{measured or extrapolated}} |
| {{dataset size}} | {{value}} | |

Beyond these figures the system is untested rather than known to fail.

## Deployment-specific caveats

- {{Constraints applying only to certain versions, platforms or configurations.}}
