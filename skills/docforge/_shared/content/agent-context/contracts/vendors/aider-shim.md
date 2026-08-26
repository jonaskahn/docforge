# `vendor-aider`

**Reader question** — "What configuration and conventions file does an Aider agent read to learn the operating kernel of this repository?"

| Mode | Depth | Shape |
|---|---|---|
| Reference | reference | fixed-frame |

Inherits [topic-view-commons.md](../references/topic-view-commons.md).

## Must present

| # | Element | At | Done wrong |
|---|---|---|---|
| 1 | A `CONVENTIONS.md` whose body is the verbatim `AGENTS.md` content | the file itself | a stale or partial copy of the kernel |
| 2 | A `.aider.conf.yml` whose `read:` list contains `AGENTS.md`, `CLAUDE.md`, `docs/agents/architecture.md`, and `.agents/rules/` without removing any pre-existing entry | the file itself | a `read:` entry removed by the merge |
