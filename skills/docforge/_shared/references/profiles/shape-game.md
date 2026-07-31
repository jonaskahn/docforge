# Shape — game

**Applies when:** the repository builds an interactive game for one or more player platforms, engines, or storefronts.

Game code is organized around frames, scenes, assets, and player-visible state. The important documentation makes runtime ownership, save compatibility, asset loading, performance targets, and platform release constraints explicit; it does not become a substitute for a game design document.

## Additions to the tree

```
docs/
├── architecture/
│   ├── gameplay-systems.md       system boundaries, update order, player state
│   └── assets-and-scenes.md      scene ownership, loading, asset pipeline
├── reference/
│   ├── performance-budgets.md    frame, memory, loading, and build-size budgets
│   └── platform-compatibility.md input, platform services, targets, caveats
└── operations/
    └── distribution.md           platform builds, signing, storefront release
```

## `architecture/gameplay-systems.md`

For each major system, name what it owns, its inputs and outputs, update or event ordering, persistence boundary, and failure behavior. Identify cross-system invariants such as authority over player state, pause semantics, and simulation determinism. Distinguish runtime behavior from intended player experience; design aspirations belong in the design source, while this document records what the shipped system guarantees.

## `architecture/assets-and-scenes.md`

Describe scene lifecycle, ownership, additive or streaming loads, asset identifiers, build-time transforms, and unloading rules. Include the user-visible result of a missing asset, corrupt save, or load timeout. State how save data is versioned and migrated, which data is account-, device-, or session-scoped, and whether a downgrade can read a newer save.

## `reference/performance-budgets.md`

Set measured budgets by target platform for frame time, memory, loading, download/build size, network latency where relevant, and battery or thermal impact on mobile hardware. Name measurement conditions and the feature that owns each budget. A target without device and scene context is not a useful budget.

## `reference/platform-compatibility.md`

List supported platforms, OS and hardware floors, input modes, display assumptions, online-service dependencies, and platform-specific degradation. Include accessibility/input remapping commitments and known storefront certification constraints when evidenced.

## `operations/distribution.md`

Document build variants, signing, content packaging, store channels, staged release or beta path, crash/telemetry ownership, and emergency rollback or hotfix process. Call out any live-content, entitlement, or save migration change that cannot be safely reversed.
