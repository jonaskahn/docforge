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

_Repeat this section once per folded flow, in `compact_order`._

{{Trigger and actors: what starts this flow and who participates.}}

```mermaid
sequenceDiagram
{{ordered interaction between the participants}}
```

{{The ordered steps, the branches that change the outcome, the rules that
govern them, the failure paths, and the final outcome — each grounded in
cited repository evidence.}}
