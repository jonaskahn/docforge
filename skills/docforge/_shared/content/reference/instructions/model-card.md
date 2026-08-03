# Model-card writing craft

Cite dataset, run or artifact, and evaluation evidence for every metric, and
name the model owner when established. Link lifecycle mechanics to
`model-lifecycle`; do not infer model quality from a declared architecture.

**Preferred illustration:** Follow
[`../../../references/illustration.md`](../../../references/illustration.md); prose
sections per Mitchell et al.'s standard shape, table only for evaluation
metrics.

Follow the Model Cards for Model Reporting shape (Mitchell et al., 2019):
model details, intended use, training data summary, evaluation results,
limitations, and out-of-scope uses, in that order. State out-of-scope uses
as plainly as intended ones.

Give evaluation results with their measurement context (dataset, metric,
date) — a bare accuracy number with no dataset named is not evidence.
Never claim a fairness or safety property the repository hasn't actually
evaluated; state what was measured and what wasn't. Link training-data
lineage to [model-lifecycle.md](model-lifecycle.md) rather than repeating
it here.
