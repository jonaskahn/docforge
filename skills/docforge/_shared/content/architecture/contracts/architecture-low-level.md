# `architecture-low-level`

**Reader question** — "Inside this block, what are the components, how do they wire together, and what happens when one call fails?"

| Mode | Depth | Shape |
|---|---|---|
| Explanation | deep-dive | answer-first |

The decisions this decomposition supports are the L0 claim; selected whiteboxes are named in full (L1) before any one component is explained (L2) — C4's Component level, zoomed in from a named high-level block.

## Must present

| # | Element | At | Done wrong |
|---|---|---|---|
| 1 | The decisions this decomposition supports, stated before any component | L0 | mechanism explained before the decisions it supports |
| 2 | Selected whitebox decompositions, under named high-level parents, all named before any one is explained | L1 | a whitebox entry that starts describing its own components before every whitebox is named |
| 3 | Component responsibility, technology, public contract, directional relationships, invariant/failure boundary | L2 | a private-symbol tour or Level-4 class prose |
| 4 | Module wiring: which components realize each cross-boundary high-level edge, with a traceability matrix | L2 | a high-level edge with no component-level realization traced |
| 5 | One distinct intra-block runtime scenario with outcome and error path | L2 | a runtime scenario with no material error path |
| 6 | Heading-level provenance for every material claim | L2 | a source citation embedded in reader-facing prose instead of provenance |
| 7 | The quality ceiling or anticipated change, only where evidenced | L3 | an estimated throughput figure with no measurement behind it |

## Keep out

| Not here | Lives in |
|---|---|
| A duplicated high-level map | `arch_high_level` |
| Level-4/class prose or a private-symbol tour | nowhere — responsibility/interface level only |
| Source citations in reader-facing prose | provenance |
| An unlabeled uses relationship | nowhere — every edge names its verb |
| Component detail inside a whitebox overview | the component's own sub-heading |
| An estimated throughput figure | nowhere — evidence-gated or omitted |
| A domain concept's meaning, invariants, or lifecycle | `concept` |

## Owns / links

| Owns | Links to | Because |
|---|---|---|
| Module/component responsibilities, one representative runtime scenario, data/control paths, failure boundaries | `arch_high_level` | every component here must trace to a block named there — no parallel decomposition |
| Which components realize each cross-boundary high-level edge | `arch_high_level` (Relationship matrix) | high-level names *that* two blocks relate; Module wiring names *which components* realize that relationship |
| A specific persisted entity or dataset touched by a component | `persistence` or `dataset` | storage mechanics are owned there; this document only names the dependency |
| A rule this component enforces on request/response shape | the owning reference document (API/config) | the observable contract is owned there; this document explains the mechanism behind it |
