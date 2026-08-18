# Model-lifecycle writing craft

- Ground each stage in dataset, training-run, artifact, and monitoring
  evidence; name the owner of each drift response.
- State concise, evidenced deployment limitations here, link detailed
  evaluation to `model-card`, and mark unevidenced bias or drift claims as
  unknown.
- Trace the full lifecycle in order: dataset lineage, training/evaluation,
  artifact packaging, inference serving, drift monitoring, ownership.
- For dataset lineage, borrow the Datasheets for Datasets discipline (Gebru
  et al., 2018): where the data came from, what it excludes, and known
  biases or gaps.
- State the artifact's provenance (which training run produced the deployed
  version) so a reader can trace a production behavior back to a specific
  training configuration.
- State drift monitoring concretely: what signal is watched, and what
  happens when it fires — retrain, roll back, or alert-only. Name the owner
  who acts on that signal.
- Detailed evaluation numbers and intended-use boundaries belong in
  `model-card`; this document owns the pipeline, not the report.

## Illustration

- **Form:** a Mermaid `flowchart` for the dataset-to-inference pipeline;
  prose for each stage's guarantee.
- **Renders:** each lifecycle stage as a node, labeled with what it hands to
  the next stage (lineage → training → artifact → serving → monitoring).
- **Trigger:** once the pipeline has more than two stages worth tracing
  together — per
  [`illustration.md`](../../../references/illustration.md)'s deep-dive budget.

## Connections

| This document owns | Links to | Because |
|---|---|---|
| Dataset lineage, training/evaluation, artifact lineage, inference, limitations, drift, ownership | `dataset` | dataset owns the training data's own identity/producers/consumers contract; this document owns the pipeline that consumes it |
| Evaluation numbers, intended-use boundaries | `model-card` (same content contract, different emphasis) | this document owns the pipeline; the card owns the report |
| A privacy boundary in the training or inference data | `security/data-handling` | data classification and handling is owned there, linked not restated |

## Voice

- **Voice:** declarative present tense, strong active verbs, no hedging.
