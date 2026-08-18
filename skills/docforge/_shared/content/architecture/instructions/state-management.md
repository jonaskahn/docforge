# State-management writing craft

- Open with the lifecycle this document covers — the named states a unit of
  state can be in, from creation to disposal.
- Trace boundaries next: what owns each piece of state, and where read access
  ends and a mutation must go through an explicit transition instead of a
  direct write.
- Walk transitions in the order they actually occur, one per short paragraph,
  naming what triggers each one and what invariant it must preserve.
- Close with failure and recovery: what happens to state on a crash
  mid-transition, whether it is durable, and how a corrupted or partial
  state is detected and repaired.
- Keep this document about lifecycle and transitions, not every field a piece
  of state happens to hold — a field inventory belongs to a reference
  document or the schema itself, linked from here.

## Illustration

- **Form:** a Mermaid `stateDiagram-v2` for the lifecycle; prose alone if
  there are fewer than three states or no branching transitions.
- **Renders:** named states and the transitions between them, each labeled
  with its trigger.
- **Trigger:** once there are three or more states or any conditional
  transition — per
  [`illustration.md`](../../../references/illustration.md)'s deep-dive
  budget (at most 8 named states).

## Connections

| This document owns | Links to | Because |
|---|---|---|
| Lifecycle, boundaries, transitions, failure/recovery | `architecture-high-level` | this is the deep-dive of the stateful block named there |
| Persisted state's storage contract | `persistence` | persistence owns durability mechanics; this document owns the state machine that uses it |
| A transition affected by UI-level state | `ui-navigation-state` | avoids re-deriving navigation state here when it is owned there |

## Voice

- **Voice:** declarative present tense, strong active verbs, no hedging.
