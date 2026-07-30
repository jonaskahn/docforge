# System-overview writing craft

**Preferred illustration:** Follow
[`../references/illustration.md`](../references/illustration.md); one C4-style
context flowchart plus one arc42-style runtime `sequenceDiagram` for the
single most architecturally relevant end-to-end path.

Keep the zoom at one level above individual flows: name the handful of major
capabilities, the components each touches, and the owning flow — then link to
`docs/flows/README.md` for the matrix rather than restating flow steps or
architecture internals. External systems appear at the boundary only.

A reader should leave knowing how features hang together across the repo, not
how any one flow executes in detail.
