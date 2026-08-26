# `vendor-codex`

**Reader question** — "What file does a Codex agent read to learn the operating kernel of this repository?"

| Mode | Depth | Shape |
|---|---|---|
| Reference | reference | fixed-frame |

Inherits [topic-view-commons.md](../references/topic-view-commons.md).

## Must present

| # | Element | At | Done wrong |
|---|---|---|---|
| 1 | A `.codex/instructions.md` whose body is the verbatim `AGENTS.md` content | the file itself | a stale or partial copy of the kernel |
| 2 | Provenance HTML comment in the first 10 lines | provenance | a missing or stale regeneration hint |

## Keep out

| Not here | Lives in |
|---|---|
| Anything outside the verbatim kernel copy | nowhere — this is a shim, not a derivation |
