# `flows_compact`

Content contract for compact document type `flows_compact`.

The merged `docs/flows.md` is the compact form of the flows section. It holds
the complete candidate matrix backed by `.docforge/flow-index.json`, followed
by one `##` section per main-priority flow the manifest folded into it. Every
candidate appears in the matrix whether or not it has a section, so coverage is
still stated in full; the section budget bounds how many flows are expanded
here, not how many are known. Each flow section carries **every field** of the
`flow` content contract, collapsing each repeated block to one line per
instance and keeping the contract's level order. Condensed, never summarized: a
folded flow that has lost its failure categories or its branch conditions is a
defect.

| Type | Must present | Keep out | Primary mode | Depth |
|---|---|---|---|---|
| flows_compact | section introduction, at-a-glance flow shape, the complete candidate matrix (entry reference, area, confidence, reach, priority, status), one section per folded flow carrying its guarantee before any mechanism, trigger, actors, ordered steps, branches, rules, failure paths each with its category, and outcome — plus data in play, timing and limits, and the observability signal where evidenced; links to every selected, materialized document in this section's folder that this file does not merge | speculative flows with no evidence row, implementation walkthroughs of a single function, direct source-file navigation, a deferred candidate written up as if it had been analyzed, a folded flow summarized rather than condensed | Explanation | deep-dive |
