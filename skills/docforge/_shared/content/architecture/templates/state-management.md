# State management

_Last reviewed: {{YYYY-MM-DD}}_

```mermaid
stateDiagram-v2
  [*] --> Created
  Created --> Active
  Active --> Active
  Active --> Disposed
  Disposed --> [*]
```

_Repeat the `##` block below per state domain — not per instance of a
state's value._

## {{State domain}}

**Owner:** {{who mutates this}}

**Read by:** {{consumers}}

**Synchronization:** {{how concurrent readers/writers stay consistent, or
`single-writer, no conflict possible`}}

**Cache invalidation:** {{what clears a stale copy, or `not cached`}}

**On bad transition:** {{failure/recovery behavior}}

Render lifecycle: see [rendering.md](rendering.md).
