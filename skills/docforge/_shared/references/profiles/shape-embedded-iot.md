# Shape — embedded / IoT firmware

**Applies when:** the repository builds firmware or software that directly controls hardware, sensors, actuators, or connected devices.

Embedded software has physical consequences and constrained recovery paths. Documentation must connect firmware behavior to the exact hardware, resource limits, protocol contracts, update trust chain, and safe state when power, connectivity, or an update fails.

## Additions to the tree

```
docs/
├── architecture/
│   ├── hardware-map.md           board variants, interfaces, pin/peripheral ownership
│   └── firmware-lifecycle.md     boot, provisioning, operation, update, recovery
├── reference/
│   └── performance-budgets.md    memory, CPU, timing, power, storage budgets
└── operations/
    └── flashing-and-recovery.md  build provenance, flashing, rollback, field recovery
```

## `architecture/hardware-map.md`

Map every supported board or revision to its processor, memory, storage, power source, sensors, actuators, buses, and externally exposed interfaces. State pin/peripheral ownership and incompatible variants. Include safe electrical or operational limits only where they are an evidenced product contract; never invent safety limits from source code.

## `architecture/firmware-lifecycle.md`

Trace boot, identity/provisioning, normal operation, connectivity loss, low-power states, reset/watchdog recovery, firmware update, and factory or field recovery. For each transition, name persisted state, authentication or signature checks, rollback criteria, and the safe behavior if it is interrupted. An update flow is incomplete unless it explains how an interrupted or invalid image avoids bricking the device.

## Protocols, data, and security

For each device-facing or cloud-facing protocol, document message ownership, versioning, authentication, replay or ordering assumptions, retry behavior, and data retained on the device. Record how device identity, credentials, and secure update material are provisioned, rotated, and revoked. Make the device's behavior without network access explicit.

## `reference/performance-budgets.md`

State RAM, flash/storage, CPU, latency/jitter, power, thermal, and wear/endurance budgets with their measurement conditions. Link each hard real-time or safety-relevant deadline to its monitor or failure response. State headroom, not merely current usage, so maintainers can judge a change safely.

## `operations/flashing-and-recovery.md`

Give reproducible build provenance, required tool and hardware versions, image selection, flashing/verification steps, logs or indicators that prove success, and recovery for a failed flash. Separate factory and field procedures, identify who may perform each, and include key/credential handling so recovery does not weaken device security.
