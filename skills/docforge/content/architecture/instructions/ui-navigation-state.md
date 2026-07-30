# Ui-navigation-state writing craft

**Preferred illustration:** Follow
[`../../../references/illustration.md`](../../../references/illustration.md); a
Mermaid `stateDiagram-v2` for navigation states, prose for state
ownership.

Name each navigation surface, who owns its state (a global store, local
component state, the platform's own navigation stack), and how state
survives or resets across a transition. State restoration behavior on
process death and error presentation per surface — a navigation document
that never says what the user sees on an error is incomplete. Keep visual
design tokens out; that's a styling concern, not navigation.
