# Data-flow writing craft

**Preferred illustration:** Follow
[`../../../references/illustration.md`](../../../references/illustration.md); a Mermaid
flowchart for the producer-to-consumer path, prose for each transformation's
contract.

Trace one lineage per section: producer, each transformation in order, and
every consumer — the data-contract pattern (a named owner and an explicit
compatibility promise per handoff), not an unbounded diagram of everything
that touches the data. State what each transformation guarantees about its
output (schema, ordering, completeness) as a contract the next stage can
rely on, not as an implementation description — a reader integrating
downstream needs to know what they can depend on, not how the stage is
coded.

Name the schema's owning document at each handoff rather than repeating
field definitions inline; this document traces movement and transformation,
[data-types.md](data-types.md) owns representation. End each traced flow
with its failure and recovery behavior — what happens to in-flight data on
a stage failure, and whether the pipeline replays, drops, or dead-letters
it; a lineage diagram without failure behavior tells only the happy-path
story.
