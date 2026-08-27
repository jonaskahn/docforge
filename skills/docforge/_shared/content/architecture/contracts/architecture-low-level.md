# `architecture-low-level`

**Reader question** — "Inside this block, what are the components, how do they wire together, and what happens when one call fails?"

| Mode | Depth | Shape |
|---|---|---|
| Explanation | deep-dive | answer-first |

The decisions this decomposition supports are the L0 claim; selected whiteboxes are named in full (L1) before any one component is explained (L2) — C4's Component level, zoomed in from a named high-level block. It is the **whole-system integration map**, not an exhaustive subsystem dump: every selected whitebox is named before any is decomposed, cross-whitebox wiring traces back to high-level relationships, and every high-level block that is intentionally not decomposed is stated as such. Small repositories without a subsystem deep dive may fully decompose up to three whiteboxes inline.

## Must present

| # | Element | At | Done wrong |
|---|---|---|---|
| 1 | The decisions this decomposition supports, stated before any component | L0 | mechanism explained before the decisions it supports |
| 2 | Selected whitebox decompositions, under named high-level parents, **all named before any one is explained** | L1 | a whitebox entry that starts describing its own components before every whitebox is named |
| 3 | Component responsibility, technology, public contract, directional relationships, invariant/failure boundary | L2 | a private-symbol tour or Level-4 class prose |
| 4 | Module wiring: which components realize each cross-boundary high-level edge, with a traceability matrix | L2 | a high-level edge with no component-level realization traced |
| 5 | One to three architecturally significant runtime scenarios, each with a successful outcome and a material error path | L2 | a runtime scenario with no material error path |
| 6 | Data/state ownership boundaries | L2 | a state claim with no owning component |
| 7 | Cross-cutting concern ownership | L3 | a concern described as handled with no owner named |
| 8 | A clear statement for every high-level block intentionally not decomposed | L3 | a silently missing whitebox that reads as "handled" |
| 9 | Links to subsystem deep dives for every block that earned one | L3 | a deep-dive destination with no link |
| 10 | Heading-level provenance for every material claim | L2 | a source citation embedded in reader-facing prose instead of provenance |
| 11 | The quality ceiling or anticipated change, only where evidenced | L3 | an estimated throughput figure with no measurement behind it |

## Keep out

| Not here | Lives in |
|---|---|
| A duplicated high-level map | `arch_high_level` |
| Subsystem internals that earned a deep dive | `architecture_subsystem` |
| Level-4/class prose or a private-symbol tour | nowhere — responsibility/interface level only |
| Source citations in reader-facing prose | provenance |
| An unlabeled uses relationship | nowhere — every edge names its verb |
| Component detail inside a whitebox overview | the component's own sub-heading |
| An estimated throughput figure | nowhere — evidence-gated or omitted |
| A domain concept's meaning, invariants, or lifecycle | `concept` |

## Owns / links

| Owns | Links to | Because |
|---|---|---|
| Module/component responsibilities, representative runtime scenarios, data/control paths, failure boundaries, cross-whitebox wiring | `arch_high_level` | every component here must trace to a block named there — no parallel decomposition |
| Which components realize each cross-boundary high-level edge | `arch_high_level` (Relationship matrix) | high-level names *that* two blocks relate; Module wiring names *which components* realize that relationship |
| A specific persisted entity or dataset touched by a component | `persistence` or `dataset` | storage mechanics are owned there; this document only names the dependency |
| A rule this component enforces on request/response shape | the owning reference document (API/config) | the observable contract is owned there; this document explains the mechanism behind it |
| A significant subsystem's internals | `architecture_subsystem` | the deep dive owns mechanism; this document traces the edge and links |
