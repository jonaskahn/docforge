# `model-card`

**Reader question** — "What was this model trained and evaluated on, and where does it not apply?"

| Mode | Depth | Shape |
|---|---|---|
| Explanation | deep-dive | fixed-frame |

_Aliased with: `model-lifecycle` (same content contract)._

External authority: the Model Cards for Model Reporting shape (Mitchell et al., 2019) — model details, intended use, training data summary, evaluation results, limitations, out-of-scope uses, in that fixed order.

## Must present

| # | Element | At | Done wrong |
|---|---|---|---|
| 1 | `Model details` | fixed order, first | reordering to lead with evaluation results |
| 2 | `Intended use` | fixed order, second | out-of-scope uses omitted while intended uses are stated |
| 3 | `Training data summary` | fixed order, third | training-data lineage repeated here instead of linked |
| 4 | `Evaluation results`, each metric with its measurement context (dataset, metric, date) | fixed order, fourth | a bare accuracy number with no dataset named |
| 5 | `Limitations` | fixed order, fifth | a fairness or safety property claimed but never actually evaluated |
| 6 | `Out-of-scope uses`, stated as plainly as intended ones | fixed order, last | out-of-scope uses hedged or omitted |

## Keep out

| Not here | Lives in |
|---|---|
| An unsupported quality or safety claim | nowhere — state what was measured and what wasn't |
| Training-data lineage detail | `model_lifecycle` |
| Lifecycle mechanics | `model_lifecycle` |

## Owns / links

| Owns | Links to | Because |
|---|---|---|
| Model details, intended use, evaluation, limitations, out-of-scope uses | `model_lifecycle` | lifecycle mechanics and training-data lineage are owned there, linked not repeated |
