# `hardware-map`

**Reader question** — "What board revision and peripherals does this actually run on, and what are their memory/power limits?"

| Mode | Depth | Shape |
|---|---|---|
| Explanation | deep-dive | lookup |

_Aliased with: `firmware-lifecycle` (same content contract)._

## Must present

| # | Element | At | Done wrong |
|---|---|---|---|
| 1 | One row per board or peripheral: protocol, memory and power budget, failure mode when absent or faulted | the table | generic component-datasheet prose instead of this repository's actual configuration |
| 2 | The stable board/peripheral revision and interface role | the table | an unavailable revision, budget, or fault behavior filled with a borrowed datasheet default |
| 3 | The source that establishes each material value | the table | a value stated with no cited source |

## Keep out

| Not here | Lives in |
|---|---|
| Transition validation, retry, rollback, or non-recovery behavior | `firmware_lifecycle` |
| Hands-on flashing and recovery procedure | `flashing_recovery` |
| A memory or power bound imposed by hardware itself | `architecture_constraints` |

## Owns / links

| Owns | Links to | Because |
|---|---|---|
| Boards, peripherals, protocols, memory/power, failure | `arch_high_level` | this is the deep-dive of the hardware/firmware block named there |
| A memory or power bound imposed by the hardware itself | `architecture_constraints` | an immovable hardware limit is a constraint, not restated lifecycle detail |
| A deferred firmware or hardware shortcut | `tech_debt` | fixable-by-us gaps are tracked there |
