# `constraints`

**Reader question** — "What bound on this system is immovable, and what did it force the design to do?"

| Mode | Depth | Shape |
|---|---|---|
| Explanation | deep-dive | lookup |

## Must present

| # | Element | At | Done wrong |
|---|---|---|---|
| 1 | Hard bounds with source (platform limit, regulation, third-party contract, physics) and design implication | the table | a bound with no traceable source, reading as an opinion |
| 2 | Deliberate non-goals, grouped separately from imposed bounds | the table | a non-goal (a choice the team could unmake) mixed with a true constraint |

## Keep out

| Not here | Lives in |
|---|---|
| A fixable shortcut disguised as a constraint | `tech_debt` |
| A user-visible accepted limitation | `limitations` |
| A bound restated per architecture block | the block itself links here instead |

## Owns / links

| Owns | Links to | Because |
|---|---|---|
| Hard, externally imposed, immovable bounds | `tech_debt` | fixable-by-us shortcuts are routed there instead, never cross-filed |
| — | `limitations` | deliberate, accepted, user-visible limitations are routed there instead, never cross-filed |
| A bound that shapes a specific block | `arch_high_level` (the affected block) | the block names what it is; this document says why it cannot be otherwise |
