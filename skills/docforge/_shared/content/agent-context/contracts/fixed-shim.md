# `fixed-shim`

**Reader question** — "What local, uncommitted preference does this machine carry that the shared kernel doesn't?"

| Mode | Depth | Shape |
|---|---|---|
| Reference | reference | fixed-frame |

External authority: the local-preference extension convention (e.g. `CLAUDE.local.md`) — emitted literally, with no kernel rubric of its own.

## Must present

| # | Element | At | Done wrong |
|---|---|---|---|
| 1 | The local-preference purpose and its uncommitted scope | lead | a shared project rule presented as local preference |
| 2 | The shared-behavior boundary: what this file does not override | L2 | this file silently overriding shared kernel behavior |
| 3 | A secret-handling warning | L2 | a secret written into the file instead of warned against |

## Keep out

| Not here | Lives in |
|---|---|
| Any documentation reference | nowhere — permanently isolated |
| A shared project rule | `agents-kernel` |
| A secret | nowhere — warn against it, never write one |
| Broad narrative | nowhere — this is a short, scoped file |

## Isolation

No reference in either direction: this file contains no Markdown link, URL, `@` import, or reference to any peer-agent or human-facing document. A generated non-agent document never links or mentions this file. Facts this output's own question needs are repeated here rather than pointed elsewhere — see [`document-composition.md`](../../references/document-composition.md).
