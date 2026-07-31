# Ui-navigation-state writing craft

For each surface, state allowed transitions and their owner using navigation or
code-graph evidence. Cite tested restoration and error behavior where available;
otherwise mark it unknown and link process-lifecycle behavior to its owner.

Name each navigation surface, who owns its state (a global store, local
component state, the platform's own navigation stack), and how state
survives or resets across a transition. State restoration behavior on
process death and error presentation per surface — a navigation document
that never says what the user sees on an error is incomplete. Keep visual
design tokens out; that's a styling concern, not navigation.

## Illustration

- **Form:** a Mermaid `stateDiagram-v2` for navigation states; prose for
  state ownership.
- **Renders:** named navigation surfaces as states and the transitions
  between them.
- **Trigger:** once there are three or more surfaces or any conditional
  transition — per
  [`illustration.md`](../../../references/illustration.md)'s deep-dive
  budget (at most 8 named states).

## Connections

| This document owns | Links to | Because |
|---|---|---|
| Surfaces, navigation, state ownership, transitions, restoration, error presentation | `ui-components` | visual design tokens are owned there; this document owns only navigation state |
| Restoration behavior after an app-lifecycle transition | `application-lifecycle` | process-death restoration is a lifecycle concern owned there, linked not restated |
