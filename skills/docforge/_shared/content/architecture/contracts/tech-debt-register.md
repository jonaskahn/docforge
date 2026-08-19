# `tech-debt-register`

**Reader question** — "What shortcut was taken here, and what does it cost us to leave it in place?"

| Mode | Depth | Shape |
|---|---|---|
| Reference | deep-dive | entry-catalog |

## Must present

| # | Element | At | Done wrong |
|---|---|---|---|
| 1 | One entry per shortcut, named by the shortcut itself ("the retry loop has no backoff"), not a vague quality label | per entry | a vague quality label ("reliability issues") instead of naming the shortcut |
| 2 | Consequence, evidence, remediation direction, in that sequence | per entry | a severity adjective substituting for evidence-backed specificity |
| 3 | Deliberate-and-prudent vs. inadvertent framing, per Fowler's quadrant | per entry | debt cross-filed as a constraint or limitation |
| 4 | Entries ordered by cost if left untouched, or proximity to the next touch | the table | alphabetical or discovery-date ordering |

## Keep out

| Not here | Lives in |
|---|---|
| A hard, externally imposed bound | `architecture_constraints` |
| A deliberate, accepted, user-visible boundary | `limitations` |
| A remediation owner not established by evidence | nowhere — retain as unowned |

## Owns / links

| Owns | Links to | Because |
|---|---|---|
| Shortcut, consequence, evidence, remediation direction | `architecture_constraints` | hard, externally imposed bounds are routed there instead — never cross-filed |
| — | `limitations` | deliberate, accepted, user-visible boundaries are routed there instead — never cross-filed |
| A debt item affecting a named architecture block | `arch_high_level` or `arch_low_level` | links back so a reader on that block sees the debt without this register restating the architecture |
