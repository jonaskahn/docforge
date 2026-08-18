# {{TITLE}}

_Last reviewed: {{YYYY-MM-DD}}_

{{Two or three sentences introducing the compact flows section: what kinds of
work this system performs end to end, and which flow a reader should follow
first. A reader with no prior project knowledge should be able to pick a
starting point.}}

## At a glance

{{The flow shape of the system: the areas work moves through and how the
flows below relate. Establish the shape; the sections below own the detail.}}

## Scope and boundaries

{{What belongs in the flows section, and what is owned by an adjacent section
instead. Name the neighbouring sections so a reader who landed here by
mistake can route themselves away. Link any document in this folder that this
file does not merge.}}

## Flow candidate matrix

| Flow | Entry reference | Area | Confidence | Reach | Priority | Status |
|---|---|---|---|---|---|---|
| [{{flow}}](#{{flow-anchor}}) | {{symbol}} | {{area}} | {{high/medium/low}} | {{n}} | main | documented below |
| {{flow}} | {{symbol}} | {{area}} | {{...}} | {{n}} | deferred | matrix only |

{{One or two sentences on how to read the matrix and what a deferred row
means: the candidate is evidenced and known, and has not been expanded here.}}

## {{Flow name}}

_Repeat this section once per folded flow, in `compact_order`. Every field of
the `flow` contract appears below; each repeated block collapses to one line
per instance, and nothing nests past `##`._

**Guarantee:** {{what a caller can rely on when this flow succeeds}}

**Trigger:** {{event, request, or schedule — name the kind}} · **Initiated by:** {{who or what starts it}} · **Preconditions:** {{what must already hold, or "none"}}

**Actors:** {{visible participants, then the ones behind the scenes}}

**Data in play:** {{what it reads and what it durably writes. Delete this line when unevidenced.}}

**Timing and limits:** {{evidenced timeouts, retries, batch sizes, rate limits. Delete this line rather than estimate.}}

```mermaid
sequenceDiagram
{{ordered interaction between the participants}}
```

**Happy path:**

1. {{observable action}}
2. {{observable action}}
3. {{outcome}}

{{Number the steps flat — compact never uses milestone sub-headings.}}

**Branches:** {{one line per branch: the condition, what happens instead, and where it rejoins. "No branches — every trigger reaches the same outcome" when there are none. Most common first.}}

**Rules:** {{one line per business rule that constrains this flow without creating a branch, linked to its owner when it governs 3+ flows, or "none beyond the branches above".}}

**Failures:** {{one line per evidenced failure: its category — decision point, awaited external event, timeout, interruption during a step, or system-wide cancellation — then how it is detected, the immediate response, and the recovery. Most severe first. A retry the caller never observes is mechanism, not a failure.}}

**Observability:** {{the log line, metric, or trace span that shows this ran, and its healthy value. Delete this line when unevidenced.}}

**Outcome:** {{on success — the durable change; on safe failure — what stays true anyway; deferred work, or "none".}}
