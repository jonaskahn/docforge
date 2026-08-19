# Architecture writing craft

Writing-craft instructions for `architecture` group documents. Routes:

- `arch_high_level` → [High-level architecture writing craft](#high-level-architecture-writing-craft)
- `arch_low_level` → [Low-level architecture writing craft](#low-level-architecture-writing-craft)
- `system_overview` → [System-overview writing craft](#system-overview-writing-craft)
- `concept` → [Concept writing craft](#concept-writing-craft)
- `architecture_constraints` → [Constraints writing craft](#constraints-writing-craft)
- `infra_environments` → [Environments writing craft](#environments-writing-craft)
- `infra_network` → [Network writing craft](#network-writing-craft)
- `dependencies` → [Dependency-inventory writing craft](#dependency-inventory-writing-craft)
- `tech_debt` → [Technical-debt writing craft](#technical-debt-writing-craft)
- `data_flow` → [Data-flow writing craft](#data-flow-writing-craft)
- `dataset` → [Dataset writing craft](#dataset-writing-craft)
- `persistence` → [Persistence writing craft](#persistence-writing-craft)
- `worker_triggers` → [Triggers-and-jobs writing craft](#triggers-and-jobs-writing-craft)
- `app_lifecycle` → [Application-lifecycle writing craft](#application-lifecycle-writing-craft)
- `platform_integration` → [Platform-integration writing craft](#platform-integration-writing-craft)
- `pwa_installation` → [Offline-installation writing craft](#offline-installation-writing-craft)
- `web_rendering` → [Rendering writing craft](#rendering-writing-craft)
- `web_state` → [State-management writing craft](#state-management-writing-craft)
- `web_components` → [Ui-components writing craft](#ui-components-writing-craft)
- `app_ui_state` → [Ui-navigation-state writing craft](#ui-navigation-state-writing-craft)
- `ai_integration` → [Ai-integration writing craft](#ai-integration-writing-craft)
- `model_lifecycle` → [Model-lifecycle writing craft](#model-lifecycle-writing-craft)
- `game_assets` → [Assets-and-scenes writing craft](#assets-and-scenes-writing-craft)
- `gameplay_systems` → [Gameplay-systems writing craft](#gameplay-systems-writing-craft)
- `hardware_map` → [Hardware-map writing craft](#hardware-map-writing-craft)
- `firmware_lifecycle` → [Firmware-lifecycle writing craft](#firmware-lifecycle-writing-craft)

## Voice and linking craft

Voice for this group is owned by [`voice.md`](../../references/voice.md): declarative present tense, strong active verbs, no hedging. Name what a linked document owns before the link ("low-level is this document's zoom-in," never "see `arch_low_level`"). What each side of a link owns, and why it is linked rather than restated, is each contract's `## Owns / links` table, not this section.

## High-level architecture writing craft

- Ground every context, boundary, block, and invariant in code-graph or
  manifest evidence.
- Link implementation technology to `tech-stack`; mark an unproven boundary
  or technology choice as unknown rather than completing the diagram by
  inference.
- Map onto C4's top two levels: "System in context" is the Context diagram
  (this system as one box among the neighbors and services it borders);
  "Building blocks" is the Container diagram (the deployable pieces inside
  that box). Keep the zoom consistent within each section — never let a
  container-level block sprout component-level detail; that belongs in
  low-level.md.
- Open with a one-paragraph system frame: what this is, at the highest level,
  and the business capability it owns.
- Move from context to blocks to communication and boundaries in that order —
  a reader should be able to draw the box diagram from the prose alone.
- Carry **both** C4 views as separate diagrams: a Context diagram in "System in
  context" and a Container diagram in "Building blocks". C4 recommends each of
  them for every software development team, and they answer different reader
  questions — who borders this system, then what runs inside it. One diagram
  standing in for both is the most common way this document ends up thinner
  than the prose it sits above.
- Name responsibilities with strong verbs ("owns," "validates," "routes"),
  not passive nouns ("handling," "management"). Put invariants in a visually
  distinct section.
- Keep the document stable by design: a claim a routine refactor would falsify
  is written too close to the code and belongs in low-level.md.
- Finish with links to low-level detail, decisions, and operational
  consequences. Name the forces that shaped this shape in one short paragraph —
  the constraint, the scale it was built for, the integration it had to live
  with — and link the record that settled each. The argument and the rejected
  alternatives stay in the decision record; a reader who never opens one should
  still know *why this shape*, which is what
  [`progressive-disclosure.md`](../../references/progressive-disclosure.md)
  calls the document's L3 boundary.
- Order the document per that same reference: the capability at L0 before any
  structure, context and containers at L1, per-edge and per-boundary detail at
  L2, stability and rationale at L3.
- Every relationship is directional and uses a specific active verb. Name its
  protocol or channel when evidence establishes one; otherwise say `unknown`.
  Never combine the C4 Context and Container zooms in a single diagram — they
  are two diagrams, one per section.

## Illustration

Two views, one per section, each answering a different question. Splitting is
the remedy for density, never a violation: per
[`illustration.md`](../../references/illustration.md), complexity goes into
more diagrams, never into a bigger one.

- **Form:** a Mermaid `flowchart` in each of the two sections.
- **Renders:** *context* — this system as one box among its neighbors, naming
  each neighbor and the contract between them, never an internal;
  *containers* — the deployable blocks inside that box and how they
  communicate, each labeled with its implementing technology.
- **Trigger:** context, always. Containers, whenever more than one deployable
  block exists — which is every repository that ships more than a single
  process. The container table beside it stays: it carries technology,
  interface, boundary, and routing columns the diagram cannot.
- **Decomposed in column:** the container table's routing column, not a third
  diagram — coherence (illustration.md) rules out spending another picture on
  "where do I go to see inside this block" when a table cell answers it at
  zero illustration cost. Name the low-level whitebox that decomposes that
  block, or `—` when it has none.
- **Budget:** the orientation bound applies per diagram, not per document. If
  either view exceeds it, split by business or functional area rather than
  dropping the view.

## Low-level architecture writing craft

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

A worked example is
[`architecture.standard.example.md`](../shared/exemplars/architecture.standard.example.md),
with its folded counterpart at
[`architecture.compact.example.md`](../shared/exemplars/architecture.compact.example.md).
Read them when a field's intent is unclear; they are craft references, not
templates.

## Section-to-altitude mapping

The contract's `## Must present` `At` column names the altitude; this maps it
onto this type's actual section names: L0 is the opening framing and the
decisions this decomposition supports; L1 is `## Layout` and
`## Selected whiteboxes`; L2 is `## Components`, `## Module wiring`,
`## Runtime scenario`, `## Quality and change scenarios`, and `## Data model`;
L3 is `## Significant subsystems` and `## Cross-cutting concerns`.

`## Selected whiteboxes` names every block worth decomposing before
`## Components` explains any one of them. A whitebox entry that starts
describing its own components has jumped a level — that prose belongs under the
component's own sub-heading.

Choose runtime scenarios from four areas rather than from whatever the graph
surfaced first: an important use case or feature; an interaction at a critical
external interface; operation and administration — launch, start-up, shutdown;
an error or exception scenario. One to three, schematic rather than detailed.

In `## Cross-cutting concerns`, delete a row when the concern does not apply to
this system, but write "no evidenced path found" when it plainly should apply
and the evidence shows nothing. A silently missing row reads as "handled".

`## Quality and change scenarios` is evidence-gated: a configured limit, a
benchmark, a load test, or an extension point the code exposes. Delete the
section rather than estimate a figure.

## Illustration

Five distinct views, each in its own section. Progressive disclosure, not one
crowded picture — per
[`illustration.md`](../../references/illustration.md), including its
non-redundancy and descriptiveness rules ("Make every illustration
informative"): a specific active verb and evidenced protocol per edge, never
a generic `calls`/`uses`/`sends`/`handles`.

| View | Form | Renders | Trigger |
|---|---|---|---|
| Layout | ASCII `text` fence | the directory grouping and what each group owns | always |
| Component map | Mermaid `flowchart` | the components inside one selected whitebox and the permitted dependency direction between them | per selected whitebox with three or more components |
| Module wiring | Mermaid `flowchart` + traceability table | which components talk across whitebox boundaries, and which `high-level.md` Relationship-matrix edge each crossing realizes | always — state explicitly and omit the diagram only when every selected whitebox's edges stay internal |
| Runtime scenario | Mermaid `sequenceDiagram` | one architecturally relevant path across components, with its outcome and a material error path | one to three scenarios, chosen for architectural relevance — never a catalogue of every call |
| Data model | Mermaid `erDiagram` | the durable entities this decomposition touches and their relationships | when a persistent model exists; otherwise prose |

The deep-dive budget bounds each view separately (at most 5 sequence
participants, 8 ER entities). A view that exceeds its bound splits into two
views with one stated question each; it is never dropped to fit.

Selecting *which* whiteboxes and scenarios to draw is the judgment call:
document the important, surprising, risky, or volatile ones and leave the
normal and standardized parts out.

## System-overview writing craft

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
  [`illustration.md`](../../references/illustration.md)'s deep-dive budget.

## Concept writing craft

- One concept, one document.
- Open by naming the concept and the responsibility it owns in a single
  sentence — what would break, or who would be confused, if this concept did
  not exist.
- Trace its relationships next: what it depends on, what depends on it, and
  the boundary at which its responsibility ends and a neighboring concept's
  begins.
- State its invariants as things that must always be true, not as
  descriptions of current behavior — a reader should be able to tell the
  difference between "this is how it works today" and "this must never
  change without breaking a caller's assumption."
- Close with the failure boundary: what this concept guarantees will not
  happen, and what it explicitly does not protect against.
- Never walk the reader through the concept symbol by symbol; that tour
  belongs to the code itself, not to a document meant to outlive a refactor.

## Section-to-altitude mapping

The contract's `## Must present` `At` column names the altitude; this maps it
onto this type's actual section names: L0 is the opening sentence and the
block this concept belongs to; L1 is `## What it models` and
`## Lifecycle and states`; L2 is `## Invariants`, `## Relationships`, and
`## Failure boundary`; L3 is `## Where it lives`.

Name every state before explaining what holds at any one of them. An invariant
that only applies in one state is stated under `## Invariants` with the state
named, never smuggled into the lifecycle prose.

## Illustration

Two conditional views; a concept document commonly earns neither, and that is a
correct outcome rather than a gap.

| View | Form | Renders | Trigger |
|---|---|---|---|
| Lifecycle | Mermaid `stateDiagram-v2` | the states this concept moves through and what moves it between them | three or more states with at least one non-linear transition; ordered prose below that |
| Neighbourhood | Mermaid `flowchart` | the concept as one node among its immediate dependencies and dependents — never its internal structure | three or more related concepts whose boundaries must be seen together |

Both are bounded by
[`illustration.md`](../../references/illustration.md)'s deep-dive budget (a
state diagram at most 8 named states). Draw neither when prose holds the
relationships comfortably: the trigger is the reader's difficulty, not the
document's length.

## Constraints writing craft

- State each hard bound as a fact with a source and a consequence: what
  imposes it (a platform limit, a regulation, a third-party contract,
  physics), and what it forces the design to do or avoid. A constraint
  without a traceable source reads as an opinion, not a bound a reviewer can
  verify.
- Group deliberate non-goals separately from imposed bounds — a non-goal is a
  choice this team made and could unmake; a constraint is not.
- This document is the one place hard, externally imposed, immovable bounds
  live. Do not let a fixable shortcut drift in here disguised as a
  constraint, and do not let a user-visible accepted limitation hide here
  instead of in `limitations-register`.

## Illustration

- **Form:** a Markdown table — source, bound, consequence — over prose or a
  diagram; a constraint is a lookup fact, not a relationship.
- **Renders:** nothing beyond the table; add prose only where a single bound
  needs more than one sentence of consequence.
- **Trigger:** never for a diagram — reference-adjacent lookup content per
  [`illustration.md`](../../references/illustration.md).

## Environments writing craft

- Link every environment difference and promotion gate to deployment
  configuration, CI policy, or its operations owner.
- Keep configuration values in `reference/configuration` and record
  unverified parity or gate behavior as unknown.
- State what actually differs between environments — configuration values,
  scale, data realism, external service stubs — as a comparison table, one
  row per dimension, environments as columns; a reader should be able to
  spot every difference in one scan.
- State the promotion boundary as plainly: what must be true before a change
  moves from one environment to the next, and who owns that gate.
- State configuration ownership per environment — which team or system
  controls each environment's config.
- Keep deployment procedure out; this document describes what differs,
  `deployment` describes how to ship into it.

## Illustration

- **Form:** a Markdown table with environments as columns — almost always
  the right shape for a comparison of this kind.
- **Renders:** every dimension that differs (config, scale, data realism,
  service stubs) across environments, one row each.
- **Trigger:** never for a diagram — this is a reference-adjacent lookup
  per [`illustration.md`](../../references/illustration.md).

## Network writing craft

- Name the infrastructure or network-policy source of truth for every zone
  crossing and enforcement boundary.
- Mark unverified topology and removal-impact claims as unknown rather than
  treating a configuration snapshot as current reality.
- Draw trust zones first — public, internal, restricted — before any single
  rule.
- For each boundary crossing, state what traffic crosses it and why, not
  every open port.
- Name the enforcement mechanism per boundary (security group, network
  policy, firewall rule set) so a reader knows where to go verify the
  current state.
- State what would happen if a boundary were removed — the
  concentration-risk question `dependencies-inventory` asks about packages,
  asked here about network segmentation.

## Illustration

- **Form:** a Mermaid `flowchart` for trust zones and the traffic crossing
  them — not a full firewall-rule dump.
- **Renders:** each zone as a node and each crossing as a labeled edge
  stating its purpose.
- **Trigger:** always for this document type — zone relationships are the
  point — within
  [`illustration.md`](../../references/illustration.md)'s deep-dive budget.

## Dependency-inventory writing craft

- For every direct dependency, cite manifest, lockfile, or SBOM evidence and
  its integration path.
- Mark an unverified license, failure mode, or replacement assumption as
  unknown; do not turn package metadata into an operational claim.
- Lead with a compact risk-oriented table, ordered by criticality — the
  dependency whose failure or removal would hurt most goes first, not the
  alphabetically first package. Keep an "if it disappeared" column (or
  equivalent prose): it forces concentration-risk assessment that a plain
  package list hides.
- Always include licence for every direct dependency.
- Give short integration notes only for dependencies whose failure or
  replacement changes system behavior; a pinned linting tool doesn't need a
  paragraph.
- Group by runtime library, external service, build/tooling, and generated
  inventory.
- Keep versions and licenses scannable in the table; keep judgment —
  criticality, failure handling, replacement effort — in prose beside it,
  not squeezed into a table cell.
- Automate the exhaustive inventory; hand-write only direct dependencies and
  assessment.
- When pointing to the generated machine-readable inventory, name what kind
  it is: a CycloneDX-style SBOM (component graph, built for vulnerability
  and dependency-risk tracking) answers different questions than an
  SPDX-style one (license and provenance focus) — say which.
- Prefer SBOMs that carry the NTIA minimum fields (supplier, name, version,
  unique id such as PURL/CPE/hash, dependency relationship, SBOM author,
  timestamp).
- This document carries the judgment a generated file cannot; it does not
  restate the file's contents.

## Illustration

- **Form:** a Markdown table (criticality-ordered) is primary; a Mermaid
  `flowchart` only for an evidenced dependency map whose relationships
  matter beyond a flat list.
- **Renders:** the risk table, or (rarely) which services a critical
  dependency chains through.
- **Trigger:** the flowchart only when a dependency's blast radius spans
  more than one downstream system — per
  [`illustration.md`](../../references/illustration.md)'s deep-dive budget.

## Technical-debt writing craft

- Each entry links to code, issue, test, or incident evidence and names a
  remediation owner when established.
- Distinguish observed debt from suspected debt, and retain an unowned item
  as such instead of assigning responsibility.
- Name each debt item by the shortcut taken, not a vague quality label — "the
  retry loop has no backoff," not "reliability issues." Use the same sequence
  for every entry: mechanism, consequence, trigger for action, credible
  remediation direction.
- Frame the "why" with Fowler's technical-debt quadrant:
  deliberate-and-prudent debt ("we shipped before validating that backoff
  mattered") reads as competent judgment; inadvertent debt ("we didn't know
  this would contend under load") reads as an honest correction. Either
  framing beats a bare severity adjective.
- Order entries by the cost they impose if left untouched, or by proximity
  to the next place someone will touch that code — not alphabetically, not
  by discovery date.
- Separate debt from hard constraints, limitations, and ordinary backlog
  with one litmus: could we fix this with engineering effort? Yes → tech
  debt (a to-do with interest). No, imposed from outside (physics, law,
  vendor) → constraint (nothing to pay down). A deliberate user-visible
  boundary → limitation. Unstarted work with no shortcut in place is
  backlog, not debt.
- Never cross-file them: a constraint in the debt register is noise a reader
  cannot action, and debt dressed as a limitation hides a remediable cause.
- Prefer evidence-backed specificity over severity adjectives.

## Illustration

- **Form:** a table for comparable register fields (mechanism, consequence,
  trigger, remediation); prose for each item's judgment.
- **Renders:** nothing beyond the table — never a diagram.
- **Trigger:** never — this is a reference-depth register per
  [`illustration.md`](../../references/illustration.md).

## Data-flow writing craft

- For every handoff, identify producer, consumer, validation or check, and
  the owner of that guarantee.
- Ground the path in code or flow evidence, link schema semantics to their
  owner, and label an unevidenced guarantee as unknown.
- Trace one lineage per section: producer, each transformation in order, and
  every consumer — the data-contract pattern (a named owner and an explicit
  compatibility promise per handoff), not an unbounded diagram of everything
  that touches the data.
- State what each transformation guarantees about its output (schema,
  ordering, completeness) as a contract the next stage can rely on, not as an
  implementation description — a reader integrating downstream needs to know
  what they can depend on, not how the stage is coded.
- Name the schema's owning document at each handoff rather than repeating
  field definitions inline; this document traces movement and
  transformation, `data-types` owns representation.
- End each traced flow with its failure and recovery behavior — what happens
  to in-flight data on a stage failure, and whether the pipeline replays,
  drops, or dead-letters it; a lineage diagram without failure behavior
  tells only the happy-path story.

## Illustration

- **Form:** a Mermaid `flowchart` for the producer-to-consumer path; prose
  for each transformation's contract.
- **Renders:** each stage as a node, labeled with the guarantee it hands to
  the next stage.
- **Trigger:** once a lineage crosses more than two transformations — per
  [`illustration.md`](../../references/illustration.md)'s deep-dive budget.

## Dataset writing craft

- Open with the dataset's identity: what real-world or system entity it
  represents and the guarantee it exists to provide.
- Name every producer and every consumer explicitly.
- State schema ownership (which document or schema file is the source of
  truth for fields, so this document links rather than repeats them),
  freshness and retention (how current the data is guaranteed to be and how
  long it is kept), and failure/recovery (what happens on a bad write, a
  missed refresh, or a consumer reading stale data).
- Evidence every lineage claim — a table, a pipeline config, a schema file
  this document can point to.
- Never present a sample or a one-off observation as if it were a guarantee;
  a reference document's value is that every row can be trusted without
  re-verification.

## Illustration

- **Form:** a Markdown table for identity/producers/consumers/freshness; a
  Mermaid `erDiagram` only when durable relationships between this and other
  datasets need to be shown, not for the dataset's own field list.
- **Renders:** producer-to-dataset-to-consumer as a lookup row, or entity
  relationships when more than one dataset is involved.
- **Trigger:** an `erDiagram` only past two or more related datasets with a
  durable relationship — per
  [`illustration.md`](../../references/illustration.md)'s reference-depth
  guidance.

## Persistence writing craft

- Ground entity mappings, transaction boundaries, and atomicity claims in
  schema, migration, manifest, or code evidence.
- Name the owning component and mark unverified crash-recovery behavior as
  unknown; storage mechanics remain here, while data contract semantics stay
  with their reference owner.
- Map each entity to its storage representation — table/collection name, key
  strategy, and any denormalization that departs from the obvious mapping,
  stated with the reason.
- State the migration mechanism (tool, versioning scheme, whether migrations
  are reversible) as a fact, not a tutorial on the tool itself.
- State the transaction and consistency boundary explicitly: what operations
  are atomic together, and what consistency model applies across entities
  that aren't (eventual, read-your-writes, none).
- Close each entity or subsystem with its failure-recovery behavior — what
  happens to a write in flight during a crash — using the same
  absence-based-fact discipline `architecture-low-level` asks for invariants
  ("never partially applies a multi-entity write").

## Illustration

- **Form:** an `erDiagram` when entity relationships need it; a table for
  entity-to-storage mapping otherwise.
- **Renders:** durable relationships between entities (ER diagram), or the
  mapping from entity to storage representation (table).
- **Trigger:** the `erDiagram` only past two or more related entities whose
  relationship matters — per
  [`illustration.md`](../../references/illustration.md)'s 8-entity limit.

## Triggers-and-jobs writing craft

- Trace each trigger, schedule, and concurrency rule to scheduler, queue,
  manifest, or code evidence.
- Name an owner only when established; link recovery procedures to their
  runbook and mark inferred downstream effects as unknown.
- One entry per job or trigger, in this order: what triggers it (schedule,
  event, manual), the payload shape, concurrency behavior (can it run
  overlapping instances, and what happens if it does), and the downstream
  effect once it completes.
- Name the owner per job, not just per system.
- Keep remediation detail out — a job that's misbehaving is a `runbook`
  concern, this document describes intended behavior, not recovery.

## Illustration

- **Form:** a table per job — trigger, payload, schedule, ownership; prose
  only for downstream-effect nuance.
- **Renders:** one row per job with its concurrency behavior stated
  explicitly.
- **Trigger:** never a diagram for the register itself; per
  [`illustration.md`](../../references/illustration.md) this stays tabular.

## Application-lifecycle writing craft

- For every state and transition, name its accountable owner and cite the
  platform declaration, lifecycle handler, manifest, or tested behavior.
- Treat unproven termination, restoration, and kill behavior as unknown; link
  persisted state to its persistence owner.
- Walk states in the order the platform actually defines them (launch,
  activation, background, termination), stating per state: what triggers
  entry, what the app must do before leaving it, and restoration behavior on
  relaunch.
- State failure boundaries per transition — what happens if the app is killed
  mid-transition — rather than only the clean path.
- Keep the UI component inventory out; that's `ui-components`.

## Illustration

- **Form:** a Mermaid `stateDiagram-v2` for launch/active/background/terminated
  states.
- **Renders:** the named lifecycle states and what triggers each transition.
- **Trigger:** always for this document type, within
  [`illustration.md`](../../references/illustration.md)'s 8-state limit.

## Platform-integration writing craft

- Cite adapter, callback, manifest, or entitlement evidence for every
  integration.
- Link permission rationale to `security/platform-permissions`; record
  unavailable platform fallback or unproven permission scope as unknown
  rather than assumed.
- One section per OS service or platform adapter integrated: what it's used
  for, the permission boundary it requires (link `platform-permissions`
  rather than repeating), the callback contract, and failure/fallback
  behavior when the service is unavailable.
- Avoid a generic platform-API tutorial — describe this repository's actual
  usage, not the platform's documentation.

## Illustration

- **Form:** prose per integration; a table for the permission/callback
  surface.
- **Renders:** one row per OS service/adapter — permission required,
  callback contract, fallback behavior.
- **Trigger:** the table once more than two integrations need comparing —
  per
  [`illustration.md`](../../references/illustration.md)'s deep-dive budget.

## Offline-installation writing craft

- Ground install and cache behavior in manifests, service-worker or cache
  configuration, implementation, and offline test evidence.
- Mark untested offline/reconnect behavior as unknown and link freshness
  guarantees to their data-flow owner.
- State installability criteria first (what makes the app installable at
  all), then the cache lifecycle: what's cached, when the cache updates, and
  how a stale cache is invalidated.
- State the offline boundary explicitly — what works with no network, what
  degrades, what fails outright — and the recovery behavior when
  connectivity returns.
- Avoid a generic service-worker tutorial; describe this app's actual
  caching strategy.

## Illustration

- **Form:** a Mermaid `stateDiagram-v2` for cache/update lifecycle states.
- **Renders:** named cache states (fresh, stale, updating, invalidated) and
  what triggers each transition.
- **Trigger:** once the cache lifecycle has more than a linear happy path —
  per
  [`illustration.md`](../../references/illustration.md)'s deep-dive budget
  (at most 8 named states).

## Rendering writing craft

- State the render lifecycle (mount, update, unmount) and what triggers each
  transition.
- Keep the component catalog out — that's `ui-components`.
- `web_rendering` owns where rendering occurs, server/client handoff when
  present, loading and error presentation, and render-boundary recovery.
- State the trigger and evidence for every material transition; do not infer
  hydration, persistence, or route behavior from framework defaults.
- Link navigation, persistence, and the component catalog for facts they own.
- `web_state` (mutation authority, invalid transitions, synchronization,
  cache invalidation, recovery) is written from its own instruction
  (`state-management`).

## Illustration

- **Form:** a Mermaid `stateDiagram-v2` for lifecycle/transitions.
- **Renders:** named render/state lifecycle stages and what triggers each
  transition.
- **Trigger:** once there are three or more states or any conditional
  transition — per
  [`illustration.md`](../../references/illustration.md)'s deep-dive
  budget (at most 8 named states).

## State-management writing craft

- Open with the lifecycle this document covers — the named states a unit of
  state can be in, from creation to disposal.
- Trace boundaries next: what owns each piece of state, and where read access
  ends and a mutation must go through an explicit transition instead of a
  direct write.
- Walk transitions in the order they actually occur, one per short paragraph,
  naming what triggers each one and what invariant it must preserve.
- Close with failure and recovery: what happens to state on a crash
  mid-transition, whether it is durable, and how a corrupted or partial
  state is detected and repaired.
- Keep this document about lifecycle and transitions, not every field a piece
  of state happens to hold — a field inventory belongs to a reference
  document or the schema itself, linked from here.

## Illustration

- **Form:** a Mermaid `stateDiagram-v2` for the lifecycle; prose alone if
  there are fewer than three states or no branching transitions.
- **Renders:** named states and the transitions between them, each labeled
  with its trigger.
- **Trigger:** once there are three or more states or any conditional
  transition — per
  [`illustration.md`](../../references/illustration.md)'s deep-dive
  budget (at most 8 named states).

## Ui-components writing craft

- Cite component API or token evidence for every component claim.
- Require an evidence-backed support or degradation field, but link the
  authoritative browser matrix to `browser-support` instead of reproducing
  it here.
- One row per component: responsibility, how it composes with others (slots,
  children, props contract), and the token/theme it consumes rather than
  hardcodes.
- Never substitute a screenshot gallery for the composition contract.

## Illustration

- **Form:** a table per component for responsibility and composition — this
  is Reference depth, not a screenshot catalog.
- **Renders:** nothing beyond the table; no relationship diagram unless
  composition cannot be expressed in a row.
- **Trigger:** never a diagram — reference depth stays tabular per
  [`illustration.md`](../../references/illustration.md).

## Ui-navigation-state writing craft

- For each surface, state allowed transitions and their owner using
  navigation or code-graph evidence.
- Cite tested restoration and error behavior where available; otherwise mark
  it unknown and link process-lifecycle behavior to its owner.
- Name each navigation surface, who owns its state (a global store, local
  component state, the platform's own navigation stack), and how state
  survives or resets across a transition.
- State restoration behavior on process death and error presentation per
  surface.
- Keep visual design tokens out; that's a styling concern, not navigation.

## Illustration

- **Form:** a Mermaid `stateDiagram-v2` for navigation states; prose for
  state ownership.
- **Renders:** named navigation surfaces as states and the transitions
  between them.
- **Trigger:** once there are three or more surfaces or any conditional
  transition — per
  [`illustration.md`](../../references/illustration.md)'s deep-dive
  budget (at most 8 named states).

## Ai-integration writing craft

- State safety controls and evaluation evidence for each integration boundary;
  record missing ones as unknown.
- Cite provider configuration and call sites; link model quality to
  `model-card` or `model-lifecycle` and data classification to
  `data-handling` rather than duplicating either.
- Draw the model/provider boundary first: which calls leave the system, to
  which provider, and what crosses that boundary in each direction.
- State the prompt/input surface as a contract: what user or system input
  reaches the model, and what sanitization or scoping happens before it does.
- State output handling explicitly: shown directly to a user, used to take an
  action, or advisory only.
- Give failure and fallback behavior when the provider is unavailable or
  returns a low-confidence result.
- State the privacy boundary (does user data leave the system in the prompt,
  is it retained by the provider) as plainly as `data-handling` would for any
  other data flow.
- Never claim a model-quality property this document doesn't evaluate — that
  belongs in `model-card` when the model is one this repository trains or
  fine-tunes.

## Illustration

- **Form:** a Mermaid `flowchart` for the model/provider boundary; prose for
  safety and privacy handling.
- **Renders:** what crosses the boundary in each direction (prompt out,
  completion in) and which provider each call reaches.
- **Trigger:** once more than one provider or call path is involved — per
  [`illustration.md`](../../references/illustration.md)'s deep-dive budget.

## Model-lifecycle writing craft

- Ground each stage in dataset, training-run, artifact, and monitoring
  evidence; name the owner of each drift response.
- State concise, evidenced deployment limitations here, link detailed
  evaluation to `model-card`, and mark unevidenced bias or drift claims as
  unknown.
- Trace the full lifecycle in order: dataset lineage, training/evaluation,
  artifact packaging, inference serving, drift monitoring, ownership.
- For dataset lineage, borrow the Datasheets for Datasets discipline (Gebru
  et al., 2018): where the data came from, what it excludes, and known
  biases or gaps.
- State the artifact's provenance (which training run produced the deployed
  version) so a reader can trace a production behavior back to a specific
  training configuration.
- State drift monitoring concretely: what signal is watched, and what
  happens when it fires — retrain, roll back, or alert-only. Name the owner
  who acts on that signal.
- Detailed evaluation numbers and intended-use boundaries belong in
  `model-card`; this document owns the pipeline, not the report.

## Illustration

- **Form:** a Mermaid `flowchart` for the dataset-to-inference pipeline;
  prose for each stage's guarantee.
- **Renders:** each lifecycle stage as a node, labeled with what it hands to
  the next stage (lineage → training → artifact → serving → monitoring).
- **Trigger:** once the pipeline has more than two stages worth tracing
  together — per
  [`illustration.md`](../../references/illustration.md)'s deep-dive budget.

## Assets-and-scenes writing craft

- Open with the system's boundaries: what counts as a scene or an asset in
  this engine/project, and where the loading pipeline's responsibility starts
  and ends.
- Trace loading next in the order it actually happens (discovery, load,
  instantiation, teardown), then save-state (what is captured, what is
  regenerated instead of saved, and why), then platform-build differences
  (what changes per target platform — asset formats, streaming behavior,
  memory budgets).
- Close with failure behavior: a missing asset, a corrupted save, or a load
  timeout, and whether the game fails safe, retries, or falls back to a
  placeholder.
- Do not drift into design-document territory — describe the loading and
  scene system as it behaves today, not the creative vision for what scenes
  should eventually contain.

## Illustration

- **Form:** an ASCII `text` block for the scene/asset directory or loading
  pipeline stages; a Mermaid `stateDiagram-v2` only if scene lifecycle has
  more than a linear load-to-teardown path.
- **Renders:** the loading pipeline as an ordered stack, or scene states and
  transitions if branching exists (paused, streaming, unloading).
- **Trigger:** the state diagram only past a linear happy path — per
  [`illustration.md`](../../references/illustration.md)'s deep-dive
  budget.

## Gameplay-systems writing craft

- State each system's boundary (what it owns, what it doesn't) and its
  save-state contract — what persists across sessions and how.
- Keep design-document aspiration out; describe what's implemented, not the
  vision for it.
- Describe recovery for missing or corrupt assets and incompatible saved
  state when evidence shows it; otherwise record the behavior as unknown.
- Ground runtime behavior in code paths and build variance in manifests or
  packaging configuration; link persistence and platform-integration rather
  than copying their mechanics.
- `gameplay_systems` owns runtime system boundaries, event/update ordering,
  and save-state semantics. `game_assets` owns the scene graph, load/unload
  dependencies, asset pipeline, and target variance — written from its own
  instruction (`assets-and-scenes`).

## Illustration

- **Form:** prose per system; a table for scene/asset loading order.
- **Renders:** each system's boundary as a short paragraph; the loading
  sequence and its per-scene dependencies as a table.
- **Trigger:** the table once loading order involves more than two scenes
  or assets with dependencies between them — per
  [`illustration.md`](../../references/illustration.md)'s deep-dive budget.

## Hardware-map writing craft

- One row per board or peripheral — protocol, memory and power budget, and
  failure mode when absent or faulted.
- Avoid generic component-datasheet prose; describe this repository's actual
  configuration.
- The hardware map is reference-grade: identify the stable board or
  peripheral revision, interface role, unit-qualified memory and power
  limits, and the source that establishes each material value.
- State an unavailable revision, budget, or fault behavior as unknown rather
  than borrowing a datasheet default.
- `firmware_lifecycle` owns transition validation and retry, rollback, or
  non-recovery behavior — written from its own instruction
  (`firmware-lifecycle`); link hands-on flashing and recovery procedures to
  operations instead of duplicating them.

## Illustration

- **Form:** a table for the board/peripheral inventory; a Mermaid
  `stateDiagram-v2` for boot/update states.
- **Renders:** one row per board/peripheral (table), and named boot/update
  states with their transitions (state diagram).
- **Trigger:** the state diagram once the boot/update path has more than a
  linear happy path (any rollback or retry state) — per
  [`illustration.md`](../../references/illustration.md)'s deep-dive
  budget (at most 8 named states).

## Firmware-lifecycle writing craft

- Open with the board and peripheral inventory this firmware runs on, stated
  as the concrete hardware this document covers — not a generic embedded
  overview.
- Trace protocols next (what talks to what, over which bus or interface),
  then the boot and update states as an ordered lifecycle: power-on,
  initialization, normal operation, update entry, update application,
  rollback.
- Name memory and power behavior as constraints the lifecycle must respect
  (available flash/RAM budget, power states that gate which transitions are
  even possible), then close with failure behavior — what happens on a
  failed flash write, a brownout mid-update, or a watchdog reset, and
  whether the device fails safe, retries, or requires physical recovery.
- Do not reproduce a component datasheet; cite the concrete part and link to
  its datasheet instead of restating registers or timing tables that belong
  to the vendor's own document.

## Illustration

- **Form:** a Mermaid `stateDiagram-v2` for the boot/update lifecycle; an
  ASCII `text` block for the board/peripheral layout if a physical or bus
  topology needs showing.
- **Renders:** named lifecycle states and the transitions between them
  (state diagram), or the physical wiring/bus grouping (ASCII).
- **Trigger:** once the lifecycle has more than a linear happy path — any
  update, rollback, or failure state — per
  [`illustration.md`](../../references/illustration.md)'s deep-dive
  budget (at most 8 named states in a state diagram).
