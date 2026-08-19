# `ai-integration`

**Reader question** — "What crosses the boundary to an AI model or provider, and what happens when that call fails?"

| Mode | Depth | Shape |
|---|---|---|
| Explanation | deep-dive | answer-first |

The model/provider boundary is drawn first — which calls leave the system, to which provider — before prompt, output, or failure detail.

## Must present

| # | Element | At | Done wrong |
|---|---|---|---|
| 1 | The model/provider boundary: which calls leave the system, to which provider | L0 | safety and privacy detail stated before the boundary itself is drawn |
| 2 | The prompt/input surface as a contract: what reaches the model, what sanitization happens first | L1 | user or system input reaching the model with no stated scoping |
| 3 | Output handling: shown to a user, used to take an action, or advisory only | L1 | output handling left unstated |
| 4 | Failure and fallback when the provider is unavailable or returns low confidence | L2 | a missing safety control left unrecorded instead of marked unknown |
| 5 | The privacy boundary: does user data leave the system in the prompt, is it retained by the provider | L2 | a model-quality claim this document doesn't evaluate |

## Keep out

| Not here | Lives in |
|---|---|
| An unsupported model-quality claim | `model_lifecycle` (`model_card`), when the model is self-trained |
| Training-system documentation | `model_lifecycle` |
| Data classification detail | `data_handling` |

## Owns / links

| Owns | Links to | Because |
|---|---|---|
| Model/provider boundary, prompts/inputs, outputs, evaluation, safety, privacy, failure | `data_handling` | the privacy boundary here is the same discipline data-handling applies to any data flow; link rather than re-derive it |
| — | `threat_model` | the model/provider call is one more external trust boundary the threat model must cover |
| Model-quality or safety claims for a self-trained model | `model_lifecycle` | this document owns the integration boundary only; quality/safety evaluation belongs to the model's own lifecycle document |
