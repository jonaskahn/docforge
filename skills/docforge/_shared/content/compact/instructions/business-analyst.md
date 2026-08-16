# Writing `docs/business-analyst.md`

The compact business-analyst file. It replaces
`docs/product/business-analyst/README.md` and its three children.

Write one `##` section per member the manifest actually selected, in
`compact_order`, grounding each section from the evidence its member contract
requires:

1. `## At a glance` — business-analyst orientation: which business processes
   this system automates and where the rules live.
2. `## Process flows` — `process-flows` (actor, trigger, business-language
   steps, decision points, exceptions, outcome, owning flow links).
3. `## Business rules` — `business-rules` (stable rule id, plain-language
   statement, trigger, outcome, exceptions, enforcement evidence).
4. `## Requirements traceability` — `requirements-traceability` (requirement
   evidence, owning rule/flow, implementation, test, status).

Write in business language throughout. A reader who does not read code must be
able to follow every section; where a rule is enforced in code, cite the
evidence rather than reproducing the call chain.

State a rule once, in `## Business rules`, and link to it from the process
flow that applies it. Do not restate a rule inside a flow step.

Ground each section from the repository evidence cited in provenance — one
provenance `sections[]` entry per `##` heading. Do not add sections beyond
what the manifest's `compact_members` for this document actually lists.

**Route to any spilled sibling.** A group that reached `COMPACT_SECTION_CAP`
keeps its overflow at its own standard paths with no `README.md` above them —
if this file does not link them, nothing does. Link every selected,
materialized document in `docs/product/business-analyst/` that is not one of this file's
`compact_members`, in `## Scope and boundaries`. Routing links are not
sections: they do not violate the rule above, and `scaffold_docs --audit`
fails the document when one is missing.
