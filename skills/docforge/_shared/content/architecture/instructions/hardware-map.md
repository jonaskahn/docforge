# Hardware-map writing craft

- One row per board or peripheral — protocol, memory and power budget, and
  failure mode when absent or faulted.
- Avoid generic component-datasheet prose; describe this repository's actual
  configuration.
- The hardware map is reference-grade: identify the stable board or
  peripheral revision, interface role, unit-qualified memory and power
  limits, and the source that establishes each material value.
- State an unavailable revision, budget, or fault behavior as unknown rather
  than borrowing a datasheet default.
- `firmware_lifecycle` owns transition validation and retry, rollback, or
  non-recovery behavior — written from its own instruction
  (`firmware-lifecycle`); link hands-on flashing and recovery procedures to
  operations instead of duplicating them.

## Illustration

- **Form:** a table for the board/peripheral inventory; a Mermaid
  `stateDiagram-v2` for boot/update states.
- **Renders:** one row per board/peripheral (table), and named boot/update
  states with their transitions (state diagram).
- **Trigger:** the state diagram once the boot/update path has more than a
  linear happy path (any rollback or retry state) — per
  [`illustration.md`](../../../references/illustration.md)'s deep-dive
  budget (at most 8 named states).

## Connections

| This document owns | Links to | Because |
|---|---|---|
| Boards, peripherals, protocols, boot/update states, memory/power, failure | `architecture-high-level` | this is the deep-dive of the hardware/firmware block named there |
| A memory or power bound imposed by the hardware itself | `constraints` | an immovable hardware limit is a constraint, not restated lifecycle detail |
| A deferred firmware or hardware shortcut | `tech-debt-register` | fixable-by-us gaps are tracked there |

## Voice

- **Voice:** declarative present tense, strong active verbs, no hedging.
