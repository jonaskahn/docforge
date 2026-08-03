---
docforge_provenance:
  schema: "2.0"
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
# Assets and scenes

_Last reviewed: {{YYYY-MM-DD}}_

_One row per scene that matters for load order or platform variance — not
every asset in the project._

| Scene | Loads after | Assets | Platform build variance |
|---|---|---|---|
| {{scene}} | {{dependency}} | {{key assets}} | {{if any}} |

## Save state

{{What is captured to a save, what is regenerated instead of saved and why,
and how a save is matched back to a scene on load.}}

## Failure and recovery

- **{{Missing asset.}}** {{Fails safe, retries, or falls back to a placeholder.}}
- **{{Corrupted save.}}** {{Detection and recovery behavior.}}
- **{{Load timeout.}}** {{What the player sees, and what happens next.}}

Gameplay systems: see [gameplay-systems.md](gameplay-systems.md).
