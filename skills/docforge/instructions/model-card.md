# Model-card writing craft

**Preferred illustration:** Follow
[`../references/illustration.md`](../references/illustration.md); prose
sections per Mitchell et al.'s standard shape, table only for evaluation
metrics.

Follow the Model Cards for Model Reporting shape (Mitchell et al., 2019):
model details, intended use, training data summary, evaluation results,
limitations, and out-of-scope uses — in that order, because a reader
deciding whether to use this model needs intended use before evaluation
numbers mean anything. State out-of-scope uses as plainly as intended
ones; a model card that only says what the model is for, not what it
isn't for, invites the exact misuse this format exists to prevent.

Give evaluation results with their measurement context (dataset, metric,
date) — a bare accuracy number with no dataset named is not evidence.
Never claim a fairness or safety property the repository hasn't actually
evaluated; state what was measured and what wasn't. Link training-data
lineage to [model-lifecycle.md](model-lifecycle.md) rather than repeating
it here.
