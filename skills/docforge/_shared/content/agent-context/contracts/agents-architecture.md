# `agents-architecture`

**Reader question** — "What are this repository's components, entry points, and dependency directions, without opening a file?"

| Mode | Depth | Shape |
|---|---|---|
| Reference | deep-dive | lookup |

## Must present

| # | Element | At | Done wrong |
|---|---|---|---|
| 1 | Self-contained stack and durable component/entry-point paths | lead | a path that will move on the next refactor |
| 2 | Component responsibilities and dependency direction | L2 | dependency direction inferred rather than evidenced |
| 3 | Data boundaries and material constraints | L2 | a constraint stated with no supporting evidence |

## Keep out

| Not here | Lives in |
|---|---|
| Any documentation reference | nowhere — permanently isolated |
| Inferred rationale | nowhere — state the fact, not the guess behind it |
| An exhaustive or volatile symbol dump | nowhere — durable paths only |

## Isolation

No reference in either direction: this file contains no Markdown link, URL, `@` import, or reference to any peer-agent or human-facing document. A generated non-agent document never links or mentions this file. Facts this output's own question needs are repeated here rather than pointed elsewhere — see [`document-composition.md`](../../references/document-composition.md).
