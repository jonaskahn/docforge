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
# Architectural constraints

_Last reviewed: {{YYYY-MM-DD}}_

The hard limits this architecture imposes by design, and the things it deliberately does
not do. These are ceilings and boundaries, not defects — stating them prevents wasted
effort and sets honest expectations under review.

## Ceilings

_A bound without a traceable source reads as an opinion, not a fact a
reviewer can verify._

| Constraint | Limit | Source | Why it exists | What lifting it would take |
|---|---|---|---|---|
| {{e.g. throughput}} | {{the ceiling}} | {{platform limit, regulation, contract, physics}} | {{the design choice behind it}} | {{the change required}} |

## Boundaries

{{What this system assumes about its environment and inputs — single region, one tenant
per instance, trusted upstream, etc. The assumptions that, if violated, break it.}}

## Non-goals

{{What this system deliberately does not do, and which component does it instead. A
reasonable person might expect these; say plainly that they are out of scope.}}

_Distinct from [tech-debt.md](tech-debt.md) (shortcuts to be paid down) and
[../reference/limitations.md](../reference/limitations.md) (feature gaps). Cross-link;
do not duplicate._
