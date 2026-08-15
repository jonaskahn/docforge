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
