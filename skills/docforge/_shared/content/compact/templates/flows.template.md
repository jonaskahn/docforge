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

_Repeat this section once per selected flow. An independent payload worker
condenses the flow's v3 `document_design` without changing its section order;
the orchestrator performs one deterministic merge. Nothing nests past `##`._

**Guarantee:** {{what a caller can rely on when this flow succeeds}}

{{ADAPTIVE_FLOW_SECTIONS}}

<!-- Condense every selected module, terminal outcome, failure/residual-state
     fact, and evidence gap from this card. Diagram forms come only from
     document_design.diagrams; there is no default sequence diagram. -->
