# Application-lifecycle writing craft

**Preferred illustration:** Follow
[`../references/illustration.md`](../references/illustration.md); a
Mermaid `stateDiagram-v2` for launch/active/background/terminated states
(bounded per illustration.md's 8-state limit).

Walk states in the order the platform actually defines them (launch,
activation, background, termination), stating per state what triggers
entry, what the app must do before leaving it, and the restoration
behavior on relaunch. State failure boundaries per transition — what
happens if the app is killed mid-transition — rather than only describing
the clean path. Keep the UI component inventory out; that's
[ui-components.md](ui-components.md).
