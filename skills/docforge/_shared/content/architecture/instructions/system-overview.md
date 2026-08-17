# System-overview writing craft

- Trace every capability, subsystem, and path to its owning flow or
  architecture source. Omit or label unresolved ownership instead of
  synthesizing a new fact; this overview connects established documents and
  does not become another owner.
- Keep the zoom at one level above individual flows: name the handful of
  major capabilities, the components each touches, and the owning flow —
  then link to `docs/flows/README.md` for the matrix rather than restating
  flow steps or architecture internals. External systems appear at the
  boundary only.
- A reader should leave knowing how features hang together across the repo,
  not how any one flow executes in detail.

## Illustration

- **Form:** one C4-style context flowchart plus one arc42-style runtime
  `sequenceDiagram` for the single most architecturally relevant end-to-end
  path.
- **Renders:** the flowchart shows major capabilities and external systems at
  the boundary; the sequence diagram shows one representative cross-capability
  path.
- **Trigger:** both, always — this document exists specifically to tie
  features together across the repo — within
  [`illustration.md`](../../../references/illustration.md)'s deep-dive budget.

## Connections

| This document owns | Links to | Because |
|---|---|---|
| The handful of major capabilities, components touched, owning flow, primary end-to-end paths, external boundary systems | `flows/flow-index` (`docs/flows/README.md`) | this document links to the flow matrix; it never restates individual flow steps |
| — | `architecture-high-level` | component detail per capability is owned there; this document only names which components a capability touches |
| — | this document is itself aligned per `document-composition.md`: it owns no new fact | every fact here must already be owned by a flow or architecture document — this is a router, exactly like `flow-index` |
