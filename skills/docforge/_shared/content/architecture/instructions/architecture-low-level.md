# Low-level architecture writing craft

- This is C4's Component level (Level 3) — the zoom-in on the containers
  named in high-level.md — so component boundaries here trace back to a
  block named there, never a parallel decomposition.
- Organize by subsystem responsibility, not directory traversal: a folder
  holding three unrelated responsibilities gets three write-ups, not one.
- Per subsystem, explain inputs, state transitions, outputs, failure
  containment, and adjacent dependencies in that order.
- Carry one view per question this document actually answers: the layout
  fence for static grouping, a component map per selected whitebox, one to
  three runtime scenarios, and an `erDiagram` when a persistent model exists.
  These are different questions, not alternatives — answering four of them
  with a single diagram is what leaves a 30 KB document carrying one visual.
- Write invariants as absence-based facts a reader cannot recover by reading
  code ("never retries a non-idempotent write").
- Close each section with the stable file/module paths that orient
  implementation work.
- `arch_low_level` is a component zoom-in and must trace each component to a
  high-level block. `concept` is a durable subsystem topic: define its
  responsibility, relationships, invariant, and failure boundary without
  forcing a parent-component decomposition.
- State only dependency semantics for data; link persistence or datasets for
  their model and storage mechanics.
- For each non-obvious failure, name evidence and the symptom or escalation
  boundary that hands control to operations or another owner.
- At `component-evidence` depth, every material responsibility and public
  contract has complete heading-level provenance. Keep paths, ranges, and
  blob hashes out of reader-facing prose.
- Keep prose at responsibility/interface level: no Level-4 code section,
  class diagram, private-symbol inventory, or directory walk.
- Each selected whitebox states why it is decomposed and the dependency
  direction it permits. The runtime scenario names its outcome and a material
  exception path; every message maps to a named component.

## Illustration

Four distinct views, each in its own section. Progressive disclosure, not one
crowded picture — per
[`illustration.md`](../../../references/illustration.md).

| View | Form | Renders | Trigger |
|---|---|---|---|
| Layout | ASCII `text` fence | the directory grouping and what each group owns | always |
| Component map | Mermaid `flowchart` | the components inside one selected whitebox and the permitted dependency direction between them | per selected whitebox with three or more components |
| Runtime scenario | Mermaid `sequenceDiagram` | one architecturally relevant path across components, with its outcome and a material error path | one to three scenarios, chosen for architectural relevance — never a catalogue of every call |
| Data model | Mermaid `erDiagram` | the durable entities this decomposition touches and their relationships | when a persistent model exists; otherwise prose |

The deep-dive budget bounds each view separately (at most 5 sequence
participants, 8 ER entities). A view that exceeds its bound splits into two
views with one stated question each; it is never dropped to fit.

Selecting *which* whiteboxes and scenarios to draw is the judgment call:
document the important, surprising, risky, or volatile ones and leave the
normal and standardized parts out.

## Connections

| This document owns | Links to | Because |
|---|---|---|
| Module/component responsibilities, one representative runtime scenario, data/control paths, failure boundaries | `architecture-high-level` (as parent zoom level) | every component here must trace to a block named there — no parallel decomposition |
| A specific persisted entity or dataset touched by a component | `persistence` or `dataset` | storage mechanics are owned there; this document only names the dependency |
| A rule this component enforces on request/response shape | `reference` (API/config) | the observable contract is owned by the reference document; this document explains the mechanism behind it |

## Voice

- **Voice:** declarative present tense, strong active verbs, no hedging.
