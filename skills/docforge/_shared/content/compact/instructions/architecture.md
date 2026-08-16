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

**Profile-driven sections follow the core.** Every document this project's
confirmed profiles and audiences select for this section folds in here too, as
its own `##` after the members listed above, in `compact_order`. Write each
from its own member contract, at its own depth — a folded profile document is
that document hosted in a shared file, not a summary of it. The manifest's
`compact_members` is the authority on which ones this project has.

**Route to any spilled sibling.** A group that reached `COMPACT_SECTION_CAP`
keeps its overflow at its own standard paths with no `README.md` above them —
if this file does not link them, nothing does. Link every selected,
materialized document in this section's folder that is not one of this file's
`compact_members`, in `## Scope and boundaries`. Routing links are not
sections: they do not violate the rule above, and `scaffold_docs --audit`
fails the document when one is missing.
