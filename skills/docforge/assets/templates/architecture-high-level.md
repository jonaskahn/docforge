---
{
  "docforge_provenance": {
    "schema": "1.0",
    "doc_id": "<DOC_ID>",
    "path": "<DOCUMENT_PATH>",
    "generated_at": "<GENERATED_AT>",
    "tool_version": "2.0.0",
    "tier": "<TIER>",
    "target_depth": "<TARGET_DEPTH>",
    "graph": {
      "provider": "<GRAPH_PROVIDER>",
      "flow": "<FLOW_CAPABILITY>"
    },
    "sections": []
  }
}
---
# High-level architecture

_Last reviewed: {{YYYY-MM-DD}}_

{{One paragraph: what this system is, at the highest level of abstraction, and the
business capability it owns.}}

## System in context

{{Where this system sits in the wider landscape — who calls it, what it calls, which
external services and systems it borders. The "part of a business" view: name the
neighbours and the contracts between them, not the internals.}}

```mermaid
flowchart LR
  U[{{actor / upstream}}] --> S[{{this system}}]
  S --> D[{{datastore / downstream}}]
  S --> X[{{external service}}]
```

## Building blocks

The major parts and what each is responsible for. One or two sentences each — behaviour,
not code. Deep mechanism lives in [low-level.md](low-level.md) and
[concepts/](concepts/README.md).

| Block | Responsibility | Boundary it owns |
|---|---|---|
| {{block}} | {{what it does}} | {{trust / API / data boundary, if any}} |

## Boundaries and data flow

{{Two or three paragraphs tracing how data and control move from input to output across
the blocks above. A reader should be able to draw the box diagram from this alone.
For the detailed flow, link [data-flow.md](data-flow.md) — do not restate it here.}}

## Stable by design

{{This document changes once or twice a year. If a claim here would be falsified by a
routine refactor, it is written too close to the code — move that detail to low-level.md.}}

## Why it is like this

Rationale lives in [decisions/](decisions/README.md). Known shortcuts live in
[tech-debt.md](tech-debt.md). Hard limits live in [constraints.md](constraints.md).
