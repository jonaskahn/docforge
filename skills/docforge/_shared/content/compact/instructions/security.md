# Writing `docs/security.md`

The compact security file. Exists only at Diligence or higher (security
content has no Spine members). Write one `##` section per member the
manifest selected, in this reading order, grounding each section from the
evidence its member contract requires:

1. `## At a glance` — folder-index orientation (security posture and scope).
2. `## Threat model` — `threat-model` (bounded DFD with zones, the
   element-by-STRIDE matrix, concrete threats each with exactly one
   disposition, testable controls/evidence, residual uncertainty, and
   accepted residual risk). Keep the analysis proportionate — the accepted-risk
   subsection is the reviewer's signal that analysis was performed. Never
   include disclosure workflow or credentials here.
3. `## Data handling` — `data-handling` (data classes, lifecycle, access,
   retention, deletion). Link `data-handling` classifications from the
   threat model above instead of restating them.

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
