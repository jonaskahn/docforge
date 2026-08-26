# `vendor-copilot`

**Reader question** — "What file does a GitHub Copilot agent read to learn the operating kernel of this repository?"

| Mode | Depth | Shape |
|---|---|---|
| Reference | reference | fixed-frame |

Inherits [topic-view-commons.md](../references/topic-view-commons.md).

## Must present

| # | Element | At | Done wrong |
|---|---|---|---|
| 1 | `.github/copilot-instructions.md` body equals the verbatim `AGENTS.md` | the file itself | a stale or partial copy of the kernel |
