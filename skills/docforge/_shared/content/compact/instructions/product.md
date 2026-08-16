# Writing `docs/product.md`

The compact product file. Write one `##` section per member, in this reading
order, grounding each section from the evidence its member contract requires:

1. `## At a glance` — folder-index orientation (what the product area covers).
2. `## Overview` — `product-overview` (users, problems, capabilities, non-goals).

Ground each section from the repository evidence cited in provenance — one
provenance `sections[]` entry per `##` heading. Do not add sections beyond the
composed contract, and do not route readers into source files.

**Route to the unfolded siblings.** Profile- and audience-driven documents
never fold, so this folder keeps static children with no `README.md` above
them — if this file does not link them, nothing does. Link every selected,
materialized document in this section's folder that is not one of this
file's `compact_members`, in `## Scope and boundaries`. Routing links are
not sections: they do not violate the rule above, and
`scaffold_docs --audit` fails the document when one is missing.
