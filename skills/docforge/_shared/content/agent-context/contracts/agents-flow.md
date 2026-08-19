# `agents-flow`

**Reader question** — "What triggers this flow, and where does it terminate, without opening the flow document?"

| Mode | Depth | Shape |
|---|---|---|
| Reference | reference | lookup |

## Must present

| # | Element | At | Done wrong |
|---|---|---|---|
| 1 | Trigger and entry path, grounded in declared flow evidence | lead | a step inferred with no flow-evidence backing |
| 2 | The durable sequence and terminal effect | L2 | a volatile call trace standing in for the durable sequence |
| 3 | Material failure behavior | L2 | business rationale not present in the evidence |

## Keep out

| Not here | Lives in |
|---|---|
| Any documentation reference | nowhere — permanently isolated |
| An inferred step with no evidence | nowhere — omit rather than guess |
| Business rationale absent from the evidence | nowhere — state the mechanism, not the motive |

## Isolation

No reference in either direction: this file contains no Markdown link, URL, `@` import, or reference to any peer-agent or human-facing document. A generated non-agent document never links or mentions this file. Facts this output's own question needs are repeated here rather than pointed elsewhere — see [`document-composition.md`](../../references/document-composition.md).
