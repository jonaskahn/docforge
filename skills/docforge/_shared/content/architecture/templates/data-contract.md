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
# Dataset: {{name}}

_Last reviewed: {{YYYY-MM-DD}}_

- **Owner:** <DATA_OWNER>
- **Location:** {{table, topic, bucket path, collection}}
- **Update cadence:** {{schedule}} · **Freshness SLA:** {{target}}
- **Grain:** one row per {{entity}} per {{period}}

## Schema

_This table is the source of truth for these fields unless a separate schema
document owns them — then delete the table and link to that document instead._

| Column | Type | Nullable | Description | PII |
|---|---|---|---|---|
| {{name}} | {{type}} | {{yes/no}} | {{meaning}} | {{none/direct/indirect}} |

## Semantics

{{Definitions of anything ambiguous: what a status value means, currency
denomination, timezone of timestamps, whether late data is restated or appended.}}

## Quality guarantees

**Enforced:** {{what is validated before publication}}

**Not enforced:** {{state the negative case explicitly}}

## Change policy

Breaking changes ({{removing or retyping a column, changing grain or semantics}})
are announced {{N}} {{days/weeks}} in advance via {{channel}}.

## Producers

| Producer | Owner | Write cadence / guarantee |
|---|---|---|
| {{producer}} | {{team/system}} | {{how often, and what it guarantees about each write}} |

## Known consumers

| Consumer | Owner | What breaks if this changes |
|---|---|---|
| {{consumer}} | {{team/system}} | {{concrete failure, not "issues"}} |

## Failure and recovery

- **{{Bad write.}}** {{What is rejected or quarantined, and who is alerted.}}
- **{{Missed refresh.}}** {{How staleness is detected and surfaced.}}
- **{{Stale read.}}** {{What a consumer sees, and how it knows the data is stale.}}
