# `firmware-lifecycle`

**Reader question** — "What hardware does this firmware run on, and what happens if an update fails mid-flash?"

| Mode | Depth | Shape |
|---|---|---|
| Explanation | deep-dive | answer-first |

The concrete board/peripheral inventory this document covers comes first, before protocols and the boot/update lifecycle.

_Aliased with: `hardware-map` (same content contract)._

## Must present

| # | Element | At | Done wrong |
|---|---|---|---|
| 1 | The board and peripheral inventory this firmware runs on, as concrete hardware | L0 | a generic embedded overview instead of this repository's actual hardware |
| 2 | Protocols: what talks to what, over which bus or interface | L1 | protocols left undescribed before the lifecycle |
| 3 | Boot and update states as an ordered lifecycle: power-on, initialization, normal operation, update entry, update application, rollback | L1 | lifecycle states presented out of actual order |
| 4 | Memory and power behavior as constraints the lifecycle must respect | L2 | a memory/power bound stated with no source |
| 5 | Failure behavior: failed flash write, brownout mid-update, watchdog reset — fails safe, retries, or requires physical recovery | L2 | a component datasheet reproduced instead of citing the part and linking its datasheet |

## Keep out

| Not here | Lives in |
|---|---|
| A reproduced component datasheet | the vendor's own datasheet, linked |
| A memory or power bound imposed by hardware itself | `architecture_constraints` |
| A deferred firmware shortcut | `tech_debt` |

## Owns / links

| Owns | Links to | Because |
|---|---|---|
| Boards, peripherals, protocols, boot/update states, memory/power, failure | `arch_high_level` | this is the deep-dive of the hardware block named there |
| A memory or power bound imposed by the hardware itself | `architecture_constraints` | an immovable hardware limit is a constraint, not restated lifecycle detail |
| A deferred firmware shortcut | `tech_debt` | fixable-by-us gaps in the update path are tracked there, not silently accepted here |
