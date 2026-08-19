# `requirements-traceability`

**Reader question** — "Which requirement produced this behavior, and how do we know it's actually satisfied?"

| Mode | Depth | Shape |
|---|---|---|
| Reference | deep-dive | coverage-matrix |

Full coverage means every evidenced requirement has a row; an incomplete chain is stated as a gap, never as proof the requirement is satisfied.

## Must present

| # | Element | At | Done wrong |
|---|---|---|---|
| 1 | Per requirement: evidence, owning rule/flow, implementation area, verification, current status | the table | an invented ticket identifier, stakeholder intent, or acceptance criterion |
| 2 | Stakeholder wording and identifiers preserved when supplied, labeled by evidence type (source, test, history, external) | the table | an incomplete chain presented as satisfying the requirement |
| 3 | A typed external token where wording or identifier is unavailable, naming the evidence needed to resolve it | the table | an external requirement invented instead of marked with a typed unknown |

## Keep out

| Not here | Lives in |
|---|---|
| An invented ticket identifier or delivery status | nowhere |
| The rule's own definition | `ba_business_rules` |
| Flow-level verification detail | the relevant `flow` document |

## Owns / links

| Owns | Links to | Because |
|---|---|---|
| The chain from evidenced requirement to rule/flow, implementation, verification | `ba_business_rules` | the rule a requirement maps to is owned there |
| Flow-level verification evidence | the relevant `flow` document | owned there, linked not repeated per requirement |
