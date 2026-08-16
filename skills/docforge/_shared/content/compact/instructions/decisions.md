# Writing `docs/decisions.md`

The compact decisions file. It replaces both
`docs/architecture/decisions/README.md` and the per-decision
`docs/architecture/decisions/{slug}.md` files a standard tree would
materialize.

Write the sections in this order:

1. `## At a glance` — what kinds of decision this repository records and how a
   reader should use them.
2. `## Decision register` — every decision the repository evidences:
   identifier, title, status, date, and superseding record where one exists.
   Give each row with a section below an anchor link to it; mark every other
   row `register only`.
3. One `##` section per decision the manifest recorded in `compact_members`,
   in `compact_order`. Write each from the `adr` contract at its normal depth
   — a folded decision is a decision record hosted in a shared file, not a
   summary of one.

**The register is the record; the sections are the budget.** The manifest
carries at most six decision sections
(`query_catalog.COMPACT_DYNAMIC_CAP`). A decision that stays a register row is
still named, dated, and status-tracked; it is never written up as though its
context and alternatives had been analyzed. Never drop a row to make room for
a section, and never add a section the manifest does not list.

Ground each section from the repository evidence cited in provenance — one
provenance `sections[]` entry per `##` heading. Decision evidence is commit
history, migration files, configuration changes, and code structure; see
[`decision-records.md`](../../../references/decision-records.md).

**Route to any spilled sibling.** A group that reached `COMPACT_SECTION_CAP`
keeps its overflow at its own standard paths with no `README.md` above them —
if this file does not link them, nothing does. Link every selected,
materialized document in `docs/architecture/decisions/` that is not one of this file's
`compact_members`, in `## Scope and boundaries`. Routing links are not
sections: they do not violate the rule above, and `scaffold_docs --audit`
fails the document when one is missing.
