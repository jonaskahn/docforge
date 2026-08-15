# Writing `docs/reference.md`

The compact reference file. Write one `##` section per member the manifest
actually selected, in this reading order, grounding each section from the
evidence its member contract requires. The fifth section exists only when
the project is compact **and** Diligence or higher.

1. `## At a glance` — folder-index orientation (what a reader can look up here).
2. `## Configuration` — `configuration` (all configuration surfaces).
3. `## Limitations` — `limitations-register` (known limits with evidence).
4. `## Technology stack` — `tech-stack` (declared dependencies and tooling).
5. `## Glossary` — `glossary` (repository terms, precise definitions, and
   which document owns each). Link to the owning section instead of
   restating a term's definition there.

Ground each section from the repository evidence cited in provenance — one
provenance `sections[]` entry per `##` heading. Do not add sections beyond
what the manifest's `compact_members` for this document actually lists, and
do not route readers into source files.
