# Writing `docs/product-owner.md`

The compact product-owner file. It replaces
`docs/product/product-owner/README.md` and its children.

Write one `##` section per member the manifest actually selected, in
`compact_order`, grounding each section from the evidence its member contract
requires:

1. `## At a glance` — product-owner orientation: what this product delivers
   and how its value is measured.
2. `## Feature catalog` — `feature-catalog` (user outcome, audience,
   availability, owning flow). Describe outcomes, not the implementation
   inventory behind them.
3. `## Success metrics` — `success-metrics` (outcome, measure, instrumentation
   state, interpretation). State the instrumentation state honestly; a target
   the repository does not carry is an external token, never a number you
   supply.
4. `## Release notes` — `release-notes` (released user impact, version/date,
   compatibility impact, feature links). Keep internal refactors and
   dependency bumps out.
5. `## Backlog traceability` — `backlog-traceability`. **This section exists
   only when the repository carries ticket evidence.** Omit the heading
   entirely rather than emitting an empty seed table, and never map a ticket
   the evidence does not support.

Ground each section from the repository evidence cited in provenance — one
provenance `sections[]` entry per `##` heading. Do not add sections beyond
what the manifest's `compact_members` for this document actually lists.

**Route to any spilled sibling.** A group that reached `COMPACT_SECTION_CAP`
keeps its overflow at its own standard paths with no `README.md` above them —
if this file does not link them, nothing does. Link every selected,
materialized document in `docs/product/product-owner/` that is not one of this file's
`compact_members`, in `## Scope and boundaries`. Routing links are not
sections: they do not violate the rule above, and `scaffold_docs --audit`
fails the document when one is missing.
