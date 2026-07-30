# Firmware-lifecycle writing craft

Open with the board and peripheral inventory this firmware runs on, stated
as the concrete hardware this document covers — not a generic embedded
overview. Trace protocols next (what talks to what, over which bus or
interface), then the boot and update states as an ordered lifecycle: power-on,
initialization, normal operation, update entry, update application, rollback.
Name memory and power behavior as constraints the lifecycle must respect
(available flash/RAM budget, power states that gate which transitions are
even possible), then close with failure behavior — what happens on a failed
flash write, a brownout mid-update, or a watchdog reset, and whether the
device fails safe, retries, or requires physical recovery.

Do not reproduce a component datasheet; cite the concrete part and link to
its datasheet instead of restating registers or timing tables that belong
to the vendor's own document.

## Illustration

- **Form:** a Mermaid `stateDiagram-v2` for the boot/update lifecycle; an
  ASCII `text` block for the board/peripheral layout if a physical or bus
  topology needs showing.
- **Renders:** named lifecycle states and the transitions between them
  (state diagram), or the physical wiring/bus grouping (ASCII).
- **Trigger:** once the lifecycle has more than a linear happy path — any
  update, rollback, or failure state — per
  [`illustration.md`](../../../references/illustration.md)'s deep-dive
  budget (at most 8 named states in a state diagram).

## Connections

| This document owns | Links to | Because |
|---|---|---|
| Boards, peripherals, protocols, boot/update states, memory/power, failure | `architecture-high-level` | this is the deep-dive of the hardware block named there |
| A memory or power bound imposed by the hardware itself | `constraints` | an immovable hardware limit is a constraint, not restated lifecycle detail |
| A deferred firmware shortcut | `tech-debt-register` | fixable-by-us gaps in the update path are tracked there, not silently accepted here |
