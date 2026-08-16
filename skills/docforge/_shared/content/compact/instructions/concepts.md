# Writing `docs/concepts.md`

The compact concepts file. It replaces both
`docs/architecture/concepts/README.md` and the per-concept
`docs/architecture/concepts/{slug}.md` files a standard tree would
materialize.

Write the sections in this order:

1. `## At a glance` — the domain vocabulary this system is built on and which
   concepts a reader must hold to follow the architecture section.
2. `## Concept register` — every discovered concept: its name, where it is
   defined in the repository, and which documents depend on it. Give each row
   with a section below an anchor link to it; mark every other row
   `register only`.
3. One `##` section per concept the manifest recorded in `compact_members`, in
   `compact_order`. Write each from the `concept` contract at full depth.

**The register is the vocabulary; the sections are the budget.** The manifest
carries at most six concept sections
(`query_catalog.COMPACT_DYNAMIC_CAP`). A register-only concept is still named
and located in the code; it is never explained as though its lifecycle and
invariants had been analyzed.

A concept belongs here only when the repository defines it. A term that needs
one sentence is a glossary entry in `docs/reference.md`, not a section here.

Ground each section from the repository evidence cited in provenance — one
provenance `sections[]` entry per `##` heading.

**Route to any spilled sibling.** A group that reached `COMPACT_SECTION_CAP`
keeps its overflow at its own standard paths with no `README.md` above them —
if this file does not link them, nothing does. Link every selected,
materialized document in `docs/architecture/concepts/` that is not one of this file's
`compact_members`, in `## Scope and boundaries`. Routing links are not
sections: they do not violate the rule above, and `scaffold_docs --audit`
fails the document when one is missing.
