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
# Model lifecycle

_Last reviewed: {{YYYY-MM-DD}}_

```mermaid
flowchart LR
  Data["{{dataset}}"] --> Train["{{training/eval}}"]
  Train --> Artifact["{{packaged artifact}}"]
  Artifact --> Serve["{{inference serving}}"]
  Serve --> Monitor["{{drift monitoring}}"]
```

## Dataset lineage

**Source:** {{where the data came from}}

**Excludes:** {{known gaps}}

**Known biases:** {{if evaluated}}

## Training and artifact

{{Training run → artifact provenance, so a production behavior traces back
to a specific configuration.}}

## Drift monitoring

**Signal watched:** {{metric}}

**On drift:** {{retrain / roll back / alert-only}}

**Owner:** {{who acts on it}}

Evaluation results and intended use: see [model-card.md](model-card.md).
