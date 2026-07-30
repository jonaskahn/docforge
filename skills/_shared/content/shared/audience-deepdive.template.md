---
docforge_provenance:
  schema: "2.0"
  doc_id: "<DOC_ID>"
  path: "<DOCUMENT_PATH>"
  generated_at: "<GENERATED_AT>"
  generator:
    name: "docforge"
    version: "2.5.0"
  tier: "<TIER>"
  target_depth: "<TARGET_DEPTH>"
  graph:
    provider: "<GRAPH_PROVIDER>"
    flow: "<FLOW_CAPABILITY>"
  sections: []
---
# {{Topic}} — {{audience: for a Business Analyst | for an engineer | for a Product Owner}}

_Last reviewed: {{YYYY-MM-DD}}_

> Depth for one reader. The plain overview and every critical notice live in
> [README.md](README.md); this file adds detail, it does not repeat the overview.

{{Write only what THIS reader needs and no other file already owns. Describe logic and
behaviour in prose. Reference files/modules by path; never paste code, never link a line
number, never hang a claim on an internal symbol a refactor would rename.}}

<!--
Shape by audience — keep the one that applies, delete the rest:

business-analyst.md
  ### Rule: {{plain-language name}}
  **Statement:** {{the rule in one sentence a stakeholder recognises}}
  **Enforced in:** {{module/file by path — the logic, not a symbol link}}
  **Applies to:** {{which flow and entity}}
  **Exceptions:** {{override conditions — usually the part code most obscures}}
  Never state a condition more precisely than the code enforces it; record ambiguity.

engineering.md
  ## Mechanism        how it actually works, step by behaviour
  ## Data model       what is stored/passed, described — not schema pasted from code
  ## Invariants       what is deliberately absent or always true, and why
  ## Failure modes    what breaks, how it degrades, what recovers it
  ## Trade-offs       what was optimised for, what was given up

product-owner.md
  ## Value            what outcome this delivers, for whom
  ## Metrics          the KPI it moves and the target → link success-metrics.md
  ## Release framing  how it reaches users; link roadmap/release-notes, don't restate dates
-->
