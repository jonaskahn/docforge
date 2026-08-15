---
docforge_provenance:
  schema: "2.1"
  doc_id: "<DOC_ID>"
  path: "<DOCUMENT_PATH>"
  generated_at: "<GENERATED_AT>"
  generator:
    name: "docforge"
    version: "2.16.0"
  tier: "<TIER>"
  target_depth: "<TARGET_DEPTH>"
  graph:
    provider: "<GRAPH_PROVIDER>"
    flow: "<FLOW_CAPABILITY>"
  sections: []
---
# Runbook: {{symptom as the pager reports it}}

_Last reviewed: {{YYYY-MM-DD}}_ · **Severity:** {{level}} · **Owner:** <TEAM_OWNER>

## Symptoms

- {{What is observed: alert name, dashboard, user-visible effect}}

## Impact

{{Who is affected and how badly. What still works.}}

## Immediate mitigation

Stop the bleeding first; diagnose afterwards.

1. `{{command}}` — {{what it does}}
2. {{step}}

## Diagnosis

1. Check {{dashboard/log/metric}}: {{what to look for}}
2. If {{condition}} → {{cause A}}, go to Resolution A.
3. If {{condition}} → {{cause B}}, go to Resolution B.

## Resolution A — {{cause}}

1. {{step}}
2. {{step}}

## Verify recovery

```bash
{{command}}
```

{{What normal looks like.}}

## Escalate

If unresolved after {{N}} minutes, escalate to <ESCALATION_OWNER> via <ESCALATION_CHANNEL>.

## Prevention

{{Known follow-up work, with tracking reference.}}
