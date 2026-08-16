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

**Route to the unfolded siblings.** Profile- and audience-driven documents
never fold, so this folder keeps static children with no `README.md` above
them — if this file does not link them, nothing does. Link every selected,
materialized document in this section's folder that is not one of this
file's `compact_members`, in `## Scope and boundaries`. Routing links are
not sections: they do not violate the rule above, and
`scaffold_docs --audit` fails the document when one is missing.
