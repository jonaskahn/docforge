# Writing `docs/flows.md`

The compact flows file. It replaces both `docs/flows/README.md` and the
per-flow `docs/flows/{slug}.md` files a standard tree would materialize.

Write the sections in this order:

1. `## At a glance` — what kinds of work this system performs end to end, and
   which flows a reader should follow first.
2. `## Flow candidate matrix` — the complete matrix from
   `.docforge/flow-index.json`: every candidate, its normalized entry
   reference, area, confidence, reach, priority, and status. Give each row
   with a section below an anchor link to it (`[Checkout](#checkout)`), and
   mark every other row `matrix only` in its status column.
3. One `##` section per flow the manifest recorded in `compact_members`, in
   `compact_order`. Write each from the `flow` contract at full deep-dive
   depth — a folded flow is a flow document hosted in a shared file, not a
   summary of one.

**The matrix is the coverage statement; the sections are the budget.** The
manifest carries at most six flow sections
(`query_catalog.COMPACT_DYNAMIC_CAP`). Deferred candidates stay matrix rows
and are never written up as though they had been analyzed. Never drop a
candidate from the matrix to make room for a section, and never add a section
the manifest does not list — `manage_manifest add --type flow` decides which
flows fold, and it refuses past the budget.

Ground each section from the repository evidence cited in provenance — one
provenance `sections[]` entry per `##` heading.

**Route to any spilled sibling.** A group that reached `COMPACT_SECTION_CAP`
keeps its overflow at its own standard paths with no `README.md` above them —
if this file does not link them, nothing does. Link every selected,
materialized document in `docs/flows/` that is not one of this file's
`compact_members`, in `## Scope and boundaries`. Routing links are not
sections: they do not violate the rule above, and `scaffold_docs --audit`
fails the document when one is missing.
