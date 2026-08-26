# `vendor-cursor`

**Reader question** — "What file does a Cursor agent read to learn the operating kernel of this repository?"

| Mode | Depth | Shape |
|---|---|---|
| Reference | reference | fixed-frame |

Inherits [topic-view-commons.md](../references/topic-view-commons.md).

## Must present

| # | Element | At | Done wrong |
|---|---|---|---|
| 1 | `.cursor/rules/agents.mdc` with MDC frontmatter `alwaysApply: true` | the file itself | a missing or wrong frontmatter key |
| 2 | Body equals the kernel content without the H1 | body | the kernel's H1 heading left in place |

## Keep out

| Not here | Lives in |
|---|---|
| Anything outside the verbatim kernel copy without H1 | nowhere — this is a shim |
