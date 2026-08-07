---
docforge_provenance:
  schema: "2.1"
  doc_id: "<DOC_ID>"
  path: "<DOCUMENT_PATH>"
  generated_at: "<GENERATED_AT>"
  generator:
    name: "docforge"
    version: "2.8.0"
  tier: "<TIER>"
  target_depth: "<TARGET_DEPTH>"
  graph:
    provider: "<GRAPH_PROVIDER>"
    flow: "<FLOW_CAPABILITY>"
  sections: []
---
# Repo inventory

_Last generated: {{YYYY-MM-DD}}_

Every repository in scope for this diligence review, assembled from declared submodules and nested repositories detected on disk. Record the evidence and the human inclusion decision for every detected member.

| Repo | Path | Membership | Docforge status (before this review) | Backfilled this review? |
|---|---|---|---|---|
| {{repo name}} | {{path relative to portfolio root}} | {{declared (submodule) / detected — not in .gitmodules / parent}} | {{none / Spine / Diligence / Portfolio}} | {{yes — selected tier / no}} |

<!-- One row per member of the collection, including the parent. Never omit
     a detected-but-excluded repo from this table — record it as excluded
     and why, rather than leaving no trace it was considered. -->
