# Dataset: {{name}}

_Last reviewed: {{YYYY-MM-DD}}_

- **Owner:** {{team or role}}
- **Location:** {{table, topic, bucket path, collection}}
- **Update cadence:** {{schedule}} · **Freshness SLA:** {{target}}
- **Grain:** one row per {{entity}} per {{period}}

## Schema

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

## Known consumers

| Consumer | Owner | What breaks if this changes |
|---|---|---|
