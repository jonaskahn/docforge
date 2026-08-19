# `model-lifecycle`

**Reader question** — "Where did this model's training data come from, and what happens when it drifts in production?"

| Mode | Depth | Shape |
|---|---|---|
| Explanation | deep-dive | ordered-narrative |

_Aliased with: `model-card` (same content contract)._

## Must present

| # | Element | At | Done wrong |
|---|---|---|---|
| 1 | The full lifecycle traced in order: dataset lineage, training/evaluation, artifact packaging, inference serving, drift monitoring, ownership | L1 | pipeline stages presented out of order |
| 2 | Dataset lineage per the Datasheets for Datasets discipline (Gebru et al., 2018): where data came from, what it excludes, known biases or gaps | L1 | dataset provenance stated with no source |
| 3 | The artifact's provenance: which training run produced the deployed version | L2 | a production behavior with no traceable training configuration |
| 4 | Drift monitoring: what signal is watched, what happens when it fires (retrain, roll back, alert-only), the owner who acts | L2 | an unevidenced bias or drift claim presented as fact |

## Keep out

| Not here | Lives in |
|---|---|
| Detailed evaluation numbers and intended-use boundaries | `model_card` |
| A privacy boundary in training or inference data | `data_handling` |

## Owns / links

| Owns | Links to | Because |
|---|---|---|
| Dataset lineage, training/evaluation, artifact lineage, inference, limitations, drift, ownership | `dataset` | dataset owns the training data's own identity/producers/consumers contract; this document owns the pipeline that consumes it |
| Evaluation numbers, intended-use boundaries | `model_card` | this document owns the pipeline; the card owns the report |
| A privacy boundary in the training or inference data | `data_handling` | data classification and handling is owned there, linked not restated |
