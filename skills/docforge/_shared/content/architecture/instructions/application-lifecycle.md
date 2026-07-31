# Application-lifecycle writing craft

For every state and transition, name its accountable owner and cite the platform
declaration, lifecycle handler, manifest, or tested behavior. Treat unproven
termination, restoration, and kill behavior as unknown; link persisted state to
its persistence owner.

Walk states in the order the platform actually defines them (launch,
activation, background, termination), stating per state what triggers
entry, what the app must do before leaving it, and the restoration
behavior on relaunch. State failure boundaries per transition — what
happens if the app is killed mid-transition — rather than only describing
the clean path. Keep the UI component inventory out; that's
[ui-components.md](ui-components.md).

## Illustration

- **Form:** a Mermaid `stateDiagram-v2` for launch/active/background/terminated
  states.
- **Renders:** the named lifecycle states and what triggers each transition.
- **Trigger:** always for this document type — the lifecycle inherently
  branches — within
  [`illustration.md`](../../../references/illustration.md)'s 8-state limit.

## Connections

| This document owns | Links to | Because |
|---|---|---|
| Launch/activation/background/termination states, ownership, restoration, failure boundaries | `ui-components` | the UI component inventory is owned there; this document only describes lifecycle states |
| Persisted state on backgrounding or restoration | `persistence` or `state-management` | what survives a lifecycle transition is owned by the state/persistence documents, linked not restated |
| A platform-imposed lifecycle bound (e.g. background execution limits) | `platform-integration` | OS-imposed lifecycle constraints are owned there; this document describes the app's own state machine |
