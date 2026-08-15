# Writing `docs/architecture.md`

The compact architecture file. Write one `##` section per member the
manifest actually selected, in this reading order, grounding each section
from the evidence its member contract requires. The first two sections exist
at every tier; the rest exist only when the project is compact **and**
Diligence or higher.

1. `## At a glance` — folder-index orientation (system mental model).
2. `## High-level architecture` — `architecture-high-level` (structure,
   boundaries, integration surfaces).
3. `## Component design` — `architecture-low-level` (selected whitebox
   decompositions, component responsibility/technology/public
   contract/directional relationships, one intra-block runtime scenario with
   its error path). Do not repeat the high-level map; go one level deeper
   only where the decomposition changes a reader's judgment.
4. `## Constraints` — `constraints` (hard bounds with source and design
   implication; deliberate non-goals). Keep temporary shortcuts and
   user-visible limitations out — those are owned elsewhere.
5. `## Dependencies` — `dependencies-inventory` (direct
   dependencies/integrations, purpose, criticality, failure behavior).
6. `## Technical debt` — `tech-debt-register` (shortcut, consequence,
   evidence, remediation direction). Keep hard constraints out — those belong
   in `## Constraints` above.

Ground each section from the repository evidence cited in provenance — one
provenance `sections[]` entry per `##` heading. Do not add sections beyond
what the manifest's `compact_members` for this document actually lists, and
do not route readers into source files.
