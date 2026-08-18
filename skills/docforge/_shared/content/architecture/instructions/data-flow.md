# Data-flow writing craft

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
  [`illustration.md`](../../../references/illustration.md)'s deep-dive budget.

## Connections

| This document owns | Links to | Because |
|---|---|---|
| Producer, each transformation, every consumer, per-handoff guarantees, failure/recovery | `dataset` | dataset owns the data's contract at rest; this document owns its movement and transformation |
| Field definitions at each handoff | the owning schema/reference document | never repeated inline; name the owner and link |
| A rule enforced during a transformation | the flow document that triggers this pipeline, if one exists | avoids re-deriving business logic already owned by a flow |

## Voice

- **Voice:** declarative present tense, strong active verbs, no hedging.
