# Rendering / state-management writing craft

Covers `web_rendering` and `web_state` — the render lifecycle and the state
that drives it are two views of the same mechanism and read better linked
than duplicated.

**Preferred illustration:** Follow
[`../../../references/illustration.md`](../../../references/illustration.md); a
Mermaid `stateDiagram-v2` for lifecycle/transitions.

For rendering: state the render lifecycle (mount, update, unmount) and
what triggers each transition. For state: state ownership boundaries (who
mutates what) and failure/recovery behavior on a bad state transition.
Keep the component catalog out — that's [ui-components.md](ui-components.md).
