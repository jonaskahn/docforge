# Writing `docs/reference.md`

The compact reference file. Write one `##` section per member, in this
reading order, grounding each section from the evidence its member contract
requires:

1. `## At a glance` — folder-index orientation (what a reader can look up here).
2. `## Configuration` — `configuration` (all configuration surfaces).
3. `## Limitations` — `limitations-register` (known limits with evidence).
4. `## Technology stack` — `tech-stack` (declared dependencies and tooling).

Ground each section from the repository evidence cited in provenance — one
provenance `sections[]` entry per `##` heading. Do not add sections beyond the
composed contract, and do not route readers into source files.
