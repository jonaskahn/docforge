# `system-overview`

**Reader question** — "How do this repo's major capabilities hang together across flows?"

| Mode | Depth | Shape |
|---|---|---|
| Explanation | deep-dive | answer-first |

An *aligned* document per `document-composition.md` — it links, it does not own new facts, exactly like `flow-index` itself. Selected only when condition `multi_flow_repo` has evidence (more than one main-priority flow).

## Must present

| # | Element | At | Done wrong |
|---|---|---|---|
| 1 | The handful of major capabilities | L0 | an invented capability with no owning flow or architecture source |
| 2 | For each, the components it touches and its owning flow | L1 | flow steps or architecture internals restated instead of linked |
| 3 | The primary end-to-end path(s) tying features together | L2 | unresolved ownership synthesized into a new fact instead of labeled |
| 4 | External systems at the boundary | L2 | a capability described in per-flow execution detail |

## Keep out

| Not here | Lives in |
|---|---|
| Restated flow steps | the owning `flow` document, linked |
| Restated architecture internals | `arch_high_level` |
| An invented capability | nowhere — trace every capability to its owning source |

## Owns / links

| Owns | Links to | Because |
|---|---|---|
| The handful of major capabilities, components touched, owning flow, primary end-to-end paths, external boundary systems | `flows_index` | this document links to the flow matrix; it never restates individual flow steps |
| — | `arch_high_level` | component detail per capability is owned there; this document only names which components a capability touches |
