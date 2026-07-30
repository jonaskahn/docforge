# Rendering / state-management writing craft

Covers `web_rendering` and `web_state` — the render lifecycle and the state
that drives it are two views of the same mechanism and read better linked
than duplicated.

For rendering: state the render lifecycle (mount, update, unmount) and
what triggers each transition. For state: state ownership boundaries (who
mutates what) and failure/recovery behavior on a bad state transition.
Keep the component catalog out — that's [ui-components.md](ui-components.md).

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
