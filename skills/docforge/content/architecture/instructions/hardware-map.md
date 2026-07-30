# Hardware-map / firmware-lifecycle writing craft

Covers `hardware_map` and `firmware_lifecycle` — the board/peripheral
inventory and the firmware states running on it are two views of the same
system.

**Preferred illustration:** Follow
[`../../../references/illustration.md`](../../../references/illustration.md); a table
for the board/peripheral inventory, a Mermaid `stateDiagram-v2` for
boot/update states.

For the hardware map: one row per board or peripheral — protocol, memory
and power budget, and failure mode when absent or faulted. For firmware
lifecycle: state boot and update states in order, and what happens on a
failed update (does it roll back, brick, or retry) — the update-failure
behavior is the single fact a reader most needs before trusting an OTA
process. Avoid generic component-datasheet prose; describe this
repository's actual configuration.
