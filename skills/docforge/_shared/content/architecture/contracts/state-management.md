# `state-management`

**Reader question** — "What states can a unit of state be in, and what happens to it on a crash mid-transition?"

| Mode | Depth | Shape |
|---|---|---|
| Explanation | deep-dive | answer-first |

The lifecycle — the named states a unit of state can be in — is the governing claim, before boundaries and transitions.

_Aliased with: `rendering` (same content contract)._

## Must present

| # | Element | At | Done wrong |
|---|---|---|---|
| 1 | The lifecycle: named states from creation to disposal | L0 | a field inventory standing in for the lifecycle |
| 2 | Boundaries: what owns each piece of state, where read access ends and mutation requires an explicit transition | L1 | a direct write where an explicit transition should be required |
| 3 | Transitions walked in the order they occur, each naming its trigger and the invariant it preserves | L1 | transitions presented out of the order they actually occur |
| 4 | Failure and recovery: state on a crash mid-transition, durability, detection and repair of a corrupted state | L2 | a mutation authority or synchronization claim with no evidence |

## Keep out

| Not here | Lives in |
|---|---|
| A field inventory | the owning reference document or schema |
| The component catalog | `web_components` |

## Owns / links

| Owns | Links to | Because |
|---|---|---|
| Lifecycle, boundaries, transitions, failure/recovery | `arch_high_level` | this is the deep-dive of the stateful block named there |
| Persisted state's storage contract | `persistence` | persistence owns durability mechanics; this document owns the state machine that uses it |
| A transition affected by UI-level state | `app_ui_state` | avoids re-deriving navigation state here when it is owned there |
