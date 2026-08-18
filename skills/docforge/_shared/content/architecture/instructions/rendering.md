# Rendering writing craft

- State the render lifecycle (mount, update, unmount) and what triggers each
  transition.
- Keep the component catalog out — that's `ui-components`.
- `web_rendering` owns where rendering occurs, server/client handoff when
  present, loading and error presentation, and render-boundary recovery.
- State the trigger and evidence for every material transition; do not infer
  hydration, persistence, or route behavior from framework defaults.
- Link navigation, persistence, and the component catalog for facts they own.
- `web_state` (mutation authority, invalid transitions, synchronization,
  cache invalidation, recovery) is written from its own instruction
  (`state-management`).

## Illustration

- **Form:** a Mermaid `stateDiagram-v2` for lifecycle/transitions.
- **Renders:** named render/state lifecycle stages and what triggers each
  transition.
- **Trigger:** once there are three or more states or any conditional
  transition — per
  [`illustration.md`](../../../references/illustration.md)'s deep-dive
  budget (at most 8 named states).

## Connections

| This document owns | Links to | Because |
|---|---|---|
| Lifecycle, boundaries, transitions, failure and recovery behavior | `ui-components` | the component catalog is owned there; this document owns only the render/state mechanism |
| Persisted state surviving a render cycle | `persistence` | durability mechanics are owned there |
| Navigation-triggered state changes | `ui-navigation-state` | avoids re-deriving navigation state here |

## Voice

- **Voice:** declarative present tense, strong active verbs, no hedging.
