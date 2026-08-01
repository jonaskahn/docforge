# architecture instructions

Writing-craft instruction files owned by the `architecture` group.

## Contents

- `ai-integration.md` — Model/provider boundary, prompts/inputs, outputs, evaluation, safety, privacy, failure → [ai-integration.md](ai-integration.md)
- `application-lifecycle.md` — Launch/activation/background/termination states, ownership, restoration, failure boundaries → [application-lifecycle.md](application-lifecycle.md)
- `architecture-high-level.md` — Context, deployable or provisioned blocks labeled with implementing technology (e.g. 'React SPA', 'PostgreSQL 15', or for `infrastructure-platform`... → [architecture-high-level.md](architecture-high-level.md)
- `architecture-low-level.md` — Module/component responsibilities and their interfaces (or, for `infrastructure-platform`, resource-group / stack responsibilities and apply order); one... → [architecture-low-level.md](architecture-low-level.md)
- `data-flow.md` — Producers, transformations, contracts, checks, failure/recovery, schema ownership → [data-flow.md](data-flow.md)
- `dependencies-inventory.md` — Direct dependencies/integrations, purpose, criticality, failure behavior → [dependencies-inventory.md](dependencies-inventory.md)
- `environments.md` — Environment differences, promotion boundaries, configuration ownership → [environments.md](environments.md)
- `gameplay-systems.md` — System boundaries, scenes/assets, loading, save state, platform builds → [gameplay-systems.md](gameplay-systems.md)
- `hardware-map.md` — Boards, peripherals, protocols, boot/update states, memory/power, failure → [hardware-map.md](hardware-map.md)
- `model-lifecycle.md` — Datasets, training/evaluation, artifact lineage, inference, limitations, drift, ownership → [model-lifecycle.md](model-lifecycle.md)
- `network.md` — Topology zones, boundary crossings, traffic purpose, enforcement, concentration-risk if a boundary is removed → [network.md](network.md)
- `offline-installation.md` — Installability, cache/update lifecycle, offline boundaries, invalidation, recovery → [offline-installation.md](offline-installation.md)
- `persistence.md` — Entities, storage mapping, migrations, transactions, consistency, failure recovery → [persistence.md](persistence.md)
- `platform-integration.md` — OS services, adapters, permissions boundary, callbacks, failure and fallback → [platform-integration.md](platform-integration.md)
- `rendering.md` — Lifecycle, boundaries, transitions, failure and recovery behavior → [rendering.md](rendering.md)
- `system-overview.md` — The handful of major capabilities; for each, the components it touches and its owning flow; the primary end-to-end path(s) tying features together; external... → [system-overview.md](system-overview.md)
- `tech-debt-register.md` — Shortcut, consequence, evidence, remediation direction → [tech-debt-register.md](tech-debt-register.md)
- `triggers-and-jobs.md` — Trigger, payload, scheduling, concurrency, ownership, downstream effects → [triggers-and-jobs.md](triggers-and-jobs.md)
- `ui-components.md` — Component responsibilities, composition, tokens/themes, browser matrix, degradation → [ui-components.md](ui-components.md)
- `ui-navigation-state.md` — Surfaces, navigation, state ownership, transitions, restoration, error presentation → [ui-navigation-state.md](ui-navigation-state.md)

## Boundaries

Files here are referenced by exact path from catalog records (`.metadata/catalog/documents/architecture/`); do not rename without updating the referencing record.
