# `ba_compact`

Content contract for compact document type `ba_compact`.

The merged `docs/business-analyst.md` is the compact form of the
business-analyst views. It holds the section-level orientation followed by
process flows, business rules, and requirements traceability — one `##`
section per member, in reading order. Each section follows its member's own
content contract; the composed contract for this document lists the members
this project's manifest actually selected. Business-analyst sections are
written in business language: a reader who does not read code must be able to
follow every one.

| Type | Must present | Keep out | Primary mode | Depth |
|---|---|---|---|---|
| ba_compact | section introduction, at-a-glance process shape, scope and boundaries, process flows (actor, trigger, business-language steps, decision points, exceptions, outcome, owning flow links), business rules (stable rule id, plain-language statement, trigger, outcome, exceptions, enforcement evidence), requirements traceability (requirement evidence, owning rule/flow, implementation, test, status); links to every selected, materialized document in this section's folder that this file does not merge | raw call chains, rules inferred only from names, invented ticket identifiers, repeated business-rule definitions, direct source-file navigation | Reference | deep-dive |
