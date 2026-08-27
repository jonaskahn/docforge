# `architecture-subsystem`

**Reader question** — "How does this significant subsystem work, where does its responsibility end, and how does it behave under failure or change?"

| Mode | Depth | Shape |
|---|---|---|
| Explanation | deep-dive | answer-first |

One bounded subsystem: the component mechanics, invariants, runtime and error scenarios, recovery, observability, and change risks a maintainer needs to hold its boundary safely. The subsystem's parent high-level block and the decisions this decomposition supports are the L0 claim; the component map is L1; per-component detail, runtime scenarios, and state behavior are L2; stability, ownership, and links are L3.

## Must present

| # | Element | At | Done wrong |
|---|---|---|---|
| 1 | Parent high-level block and the architectural decisions this decomposition supports, stated before any mechanism | L0 | mechanism explained before the boundary and decisions it serves |
| 2 | Responsibility and explicit non-responsibilities | L0 | a subsystem that quietly absorbs a neighbor's responsibility |
| 3 | Component map and component contract table | L1 | a private-symbol tour or Level-4 class prose |
| 4 | Permitted dependency direction and forbidden dependencies | L1 | an unlabeled relationship with no direction or verb |
| 5 | Inputs, outputs, public contracts, and adjacent systems | L1 | a contract asserted with no evidence, or no named neighbor |
| 6 | One or more significant runtime scenarios, each with a material failure branch | L2 | a runtime scenario with no error path |
| 7 | State/data/transaction/consistency behavior when applicable | L2 | a consistency claim with no transaction boundary |
| 8 | Failure containment, retry, rollback, degradation, and escalation boundaries | L2 | failure behavior asserted without evidence or left implicit |
| 9 | Observability signals and operational handoff | L2 | signals invented instead of read from the code |
| 10 | Security/trust implications when the subsystem crosses a boundary | L2 | a boundary crossing with no trust implication stated |
| 11 | Evidenced scaling, performance, resource, and anticipated-change scenarios | L3 | an estimated throughput figure with no measurement behind it |
| 12 | Stable implementation locations | L3 | file/module paths that a routine refactor would falsify |
| 13 | Unknowns, open risks, and links to owning specialized documents | L3 | an unevidenced claim presented as fact |

## Keep out

| Not here | Lives in |
|---|---|
| A duplicated high-level map | `arch_high_level` |
| A whole-system component walk | `arch_low_level` |
| Which subsystem documents exist and one reader question each | `architecture_subsystems_index` |
| A domain concept's meaning, invariants, lifecycle | `concept` |
| Level-4/class prose or a private-symbol tour | nowhere — responsibility/interface level only |
| Source citations in reader-facing prose | provenance |
| Storage mechanics for a persisted entity | `persistence` or `dataset` |
| Signals, alert intent, runbook diagnosis | `observability`, `runbook` |
| An estimated throughput figure | nowhere — evidence-gated or omitted |

## Owns / links

| Owns | Links to | Because |
|---|---|---|
| The subsystem's boundary, mechanisms, invariants, runtime behavior, failure/recovery, observability, change pressures | `arch_high_level` | the parent block named here must exist there; this document is the block's deep dive |
| Which components realize each cross-boundary edge into this subsystem | `arch_low_level` (Module wiring) | `arch_low_level` names the edge; this document explains the mechanism behind it |
| A specific persisted entity or dataset this subsystem owns | `persistence` or `dataset` | storage mechanics are owned there; this document only names the dependency |
| Signals and operational handoff | `observability` | alert intent and diagnosis are owned there; this document names what to watch |
| A rule this subsystem enforces on request/response shape | the owning reference document (API/config) | the observable contract is owned there; this document explains the mechanism behind it |
