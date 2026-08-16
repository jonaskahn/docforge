# `flows_compact`

Content contract for compact document type `flows_compact`.

The merged `docs/flows.md` is the compact form of the flows section. It holds
the complete candidate matrix backed by `.docforge/flow-index.json`, followed
by one `##` deep-dive section per main-priority flow the manifest folded into
it. Every candidate appears in the matrix whether or not it has a section, so
coverage is still stated in full; the section budget bounds how many flows are
expanded here, not how many are known. Each flow section follows the `flow`
content contract.

| Type | Must present | Keep out | Primary mode | Depth |
|---|---|---|---|---|
| flows_compact | section introduction, at-a-glance flow shape, the complete candidate matrix (entry reference, area, confidence, reach, priority, status), one section per folded flow carrying trigger, actors, ordered steps, branches, rules, failure paths, and outcome; links to every selected, materialized document in this section's folder that this file does not merge | speculative flows with no evidence row, implementation walkthroughs of a single function, direct source-file navigation, a deferred candidate written up as if it had been analyzed | Explanation | deep-dive |
