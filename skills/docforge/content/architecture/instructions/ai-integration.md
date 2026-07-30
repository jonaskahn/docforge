# Ai-integration writing craft

**Preferred illustration:** Follow
[`../../../references/illustration.md`](../../../references/illustration.md); a
flowchart for the model/provider boundary, prose for safety and privacy
handling.

Draw the model/provider boundary first: which calls leave the system,
to which provider, and what crosses that boundary in each direction —
this is the trust-boundary discipline threat-model.md applies to any
external dependency, applied here to a model call. State the prompt/input
surface as a contract: what user or system input reaches the model, and
what sanitization or scoping happens before it does.

State output handling explicitly: is the model's output shown directly to
a user, used to take an action, or only advisory — the failure mode differs
completely by which. Give the failure and fallback behavior when the
provider is unavailable or returns a low-confidence result. State the
privacy boundary (does user data leave the system in the prompt, is it
retained by the provider) as plainly as data-handling.md would for any
other data flow. Never claim a model-quality property this document
doesn't evaluate — that belongs in [model-card.md](model-card.md) when the
model is one this repository trains or fine-tunes.
