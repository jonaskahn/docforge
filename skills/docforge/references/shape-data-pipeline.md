# Shape — data pipeline / ETL

**Applies when:** the repo defines scheduled jobs, DAGs, extract/transform/load stages, streaming consumers, or writes to a warehouse, lake or vector store.

The distinguishing property of a data repo is that its most important interfaces are not functions but **datasets**. Consumers depend on schema, freshness and semantics — none of which appear in a code map. Two documents carry almost all the value here: the flow map and the data contracts.

## Additions to the tree

```
docs/
├── architecture/
│   ├── data-flow.md            the stage map — sources through to destinations
│   └── contracts/              one file per input source and output dataset
│       ├── README.md
│       └── <dataset-name>.md
├── engineering/
│   └── data-quality.md         validation, tests, what a failure blocks
├── operations/
│   └── runbooks/
│       ├── backfill.md
│       ├── failed-run.md
│       └── schema-change.md
└── reference/
    └── data-types.md           type mapping across system boundaries
```

## `architecture/data-flow.md`

Trace the path once, in order, then document each stage.

```markdown
# Data flow

## Overview
<Mermaid flowchart: sources → stages → destinations. Precede it with two
sentences describing the same path in prose, for renderers that show raw source.>

## Stages
### <Stage name>
- **Input:** <where from, in what shape>
- **Transformation:** what changes, in domain terms
- **Output:** <where to, in what shape>
- **Trigger:** schedule, event, or manual — with the actual cron or event name
- **Idempotency:** is a re-run safe? If not, what breaks and how is it recovered?
- **Failure behaviour:** retries, backoff, dead-letter destination, alerting
- **Typical volume and duration:** what normal looks like, so abnormal is visible
```

Idempotency and failure behaviour are the sections operators actually need at three in the morning, and the ones most often omitted. State them even when the answer is unflattering — "not idempotent; a re-run duplicates rows, recover by truncating the partition first" is exactly what the runbook needs.

## `architecture/contracts/<dataset>.md`

A data contract is a promise to downstream consumers. Write one per dataset that anything outside this repo reads.

```markdown
# Dataset: <name>

- **Owner:** <team or role>
- **Location:** <table, topic, bucket path, collection>
- **Update cadence:** <schedule> — **freshness SLA:** <target>
- **Grain:** one row per <entity per period>. The grain statement prevents more
  downstream errors than the schema does.

## Schema
| Column | Type | Nullable | Description | PII |
|---|---|---|---|---|

## Semantics
Definitions of anything ambiguous: what "active" means, how a currency amount is
denominated, what timezone a timestamp carries, whether late-arriving data is
restated or appended.

## Quality guarantees
What is validated before publication, and what is not. State the negative case:
"uniqueness of `id` is enforced; referential integrity to `customers` is not".

## Change policy
What counts as a breaking change (removing or retyping a column, changing grain
or semantics), the notice period, and how consumers are informed.

## Known consumers
Who reads this and what would break. Maintain it even approximately — an
unmaintained consumer list is still better than none when planning a change.
```

The **PII column** is not optional. Personal-data classification at the field level is what makes deletion requests, retention policy and access review tractable; retrofitting it across a mature warehouse is punishing work.

## `engineering/data-quality.md`

What is checked, where, and what happens on failure. Distinguish checks that **block publication** from checks that **warn**: consumers need to know whether a passing pipeline means clean data or merely a completed run. Cover schema validation, row-count and volume anomaly bounds, freshness, uniqueness and referential checks, and business-rule assertions.

## `reference/limitations.md` additions

Data pipelines accumulate a characteristic species of caveat that is invisible in code and expensive to rediscover. Enumerate per source and per destination:

- Minimum versions of external systems for a given capability, with the reason.
- Resource behaviours that surprise operators: replication slots growing without bound when a consumer stalls; storage costs of retained intermediate state.
- Type-mapping losses at boundaries: precision truncation, timezone flattening, values one system permits that another rejects.
- Ordering, exactly-once and late-arrival semantics — what is actually guaranteed rather than what is assumed.
- Backfill constraints: how far history goes, what a full rebuild costs in time and money.

## `reference/data-types.md`

A mapping table across every boundary the data crosses (source type → internal representation → destination type), with a notes column for lossy conversions. Anyone debugging a value that changed in flight starts here, and without it they start by reading transformation code.
