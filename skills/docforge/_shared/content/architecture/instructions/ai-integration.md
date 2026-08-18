# Ai-integration writing craft

- State safety controls and evaluation evidence for each integration boundary;
  record missing ones as unknown.
- Cite provider configuration and call sites; link model quality to
  `model-card` or `model-lifecycle` and data classification to
  `data-handling` rather than duplicating either.
- Draw the model/provider boundary first: which calls leave the system, to
  which provider, and what crosses that boundary in each direction.
- State the prompt/input surface as a contract: what user or system input
  reaches the model, and what sanitization or scoping happens before it does.
- State output handling explicitly: shown directly to a user, used to take an
  action, or advisory only.
- Give failure and fallback behavior when the provider is unavailable or
  returns a low-confidence result.
- State the privacy boundary (does user data leave the system in the prompt,
  is it retained by the provider) as plainly as `data-handling` would for any
  other data flow.
- Never claim a model-quality property this document doesn't evaluate — that
  belongs in `model-card` when the model is one this repository trains or
  fine-tunes.

## Illustration

- **Form:** a Mermaid `flowchart` for the model/provider boundary; prose for
  safety and privacy handling.
- **Renders:** what crosses the boundary in each direction (prompt out,
  completion in) and which provider each call reaches.
- **Trigger:** once more than one provider or call path is involved — per
  [`illustration.md`](../../../references/illustration.md)'s deep-dive budget.

## Connections

| This document owns | Links to | Because |
|---|---|---|
| Model/provider boundary, prompts/inputs, outputs, evaluation, safety, privacy, failure | `security/data-handling` | the privacy boundary here is the same discipline data-handling applies to any data flow; link rather than re-derive it |
| — | `security/threat-model` | the model/provider call is one more external trust boundary the threat model must cover |
| Model-quality or safety claims for a self-trained model | `model-lifecycle` (`model-card`) | this document owns the integration boundary only; quality/safety evaluation belongs to the model's own lifecycle document |

## Voice

- **Voice:** declarative present tense, strong active verbs, no hedging.
