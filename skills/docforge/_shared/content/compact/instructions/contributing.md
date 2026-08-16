# Writing `docs/contributing.md`

The compact contributing file. Exists only at Diligence or higher
(contributing content has no Spine members). Write one `##` section per
member the manifest selected, in this reading order, grounding each section
from the evidence its member contract requires:

1. `## At a glance` — folder-index orientation (how this section guides
   contributors). Link to the root `CONTRIBUTING.md` for the verified
   contribution path and required checks — that file stays separate and is
   never folded in here.
2. `## Ownership` — `ownership` (owned areas, responsibility boundaries,
   escalation tokens). Never invent people or teams the repository does not
   evidence.

Ground each section from the repository evidence cited in provenance — one
provenance `sections[]` entry per `##` heading. Do not add sections beyond
what the manifest's `compact_members` for this document actually lists, and
do not route readers into source files.

**Route to the unfolded siblings.** Profile- and audience-driven documents
never fold, so this folder keeps static children with no `README.md` above
them — if this file does not link them, nothing does. Link every selected,
materialized document in this section's folder that is not one of this
file's `compact_members`, in `## Scope and boundaries`. Routing links are
not sections: they do not violate the rule above, and
`scaffold_docs --audit` fails the document when one is missing.
