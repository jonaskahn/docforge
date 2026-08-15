---
docforge_provenance:
  schema: "2.1"
  doc_id: "<DOC_ID>"
  path: "<DOCUMENT_PATH>"
  generated_at: "<GENERATED_AT>"
  generator:
    name: "docforge"
    version: "2.15.0"
  tier: "<TIER>"
  target_depth: "<TARGET_DEPTH>"
  graph:
    provider: "<GRAPH_PROVIDER>"
    flow: "<FLOW_CAPABILITY>"
  sections: []
---
# {{NNNN}}. {{Decision stated as an outcome}}

- **Status:** {{proposed|accepted|superseded by [NNNN](NNNN-slug.md)|deprecated}}
- **Date:** {{YYYY-MM-DD}}
- **Deciders:** {{roles or names}}

## Context and problem statement

{{What forced a decision, and the constraints that were real at the time. Written
so it makes sense to someone who joins in two years knowing none of the history.}}

## Considered options

- **{{Option A}}** — {{one line}}
- **{{Option B}}** — {{one line}}
- **{{Option C}}** — {{one line}}

## Decision

We chose **{{option}}**, because {{the reasoning that was actually decisive}}.

## Decision drivers

- {{evidenced driver, or state that this is a reconstructed Nygard baseline}}

## Option comparison

| Option | Good | Neutral | Bad |
|---|---|---|---|
| {{option}} | {{evidenced benefit}} | {{tradeoff}} | {{evidenced cost}} |

## Consequences

**Positive:** {{what this buys}}

**Negative:** {{what it costs — name the real trade-off}}

**Neutral:** {{what changes without being better or worse}}

## Revisit if

{{The conditions that should trigger reconsideration: a scale threshold, a
dependency's end of life, a change in team size or requirements.}}

## Confirmation

{{For a load-bearing decision, name the concrete test, lint, review, or CI gate.
Otherwise state why a confirmation mechanism is not established.}}
