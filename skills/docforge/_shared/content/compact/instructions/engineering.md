# Writing `docs/engineering.md`

The compact engineering file. Write one `##` section per member the
manifest actually selected, in this reading order, grounding each section
from the evidence its member contract requires. The first three sections
exist at every tier; the rest exist only when the project is compact **and**
Diligence or higher — `## Conventions` additionally exists only when a
conventions source was found (same condition as the standard `conventions`
document).

1. `## At a glance` — folder-index orientation (how this repository is built
   and tested).
2. `## Setup` — `setup-guide` (getting a working checkout).
3. `## Testing` — `testing-guide` (how to run and extend the test suite).
4. `## Conventions` — `conventions` (evidenced style, structure, error
   handling, testing, and review conventions). Order dimensions by how often
   a contributor collides with them; drop any dimension the repository
   doesn't evidence.
5. `## Release` — `release-guide` (prerequisites, versioning, build,
   verification, publication, rollback).

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
