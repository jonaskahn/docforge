# `concepts_compact`

Content contract for compact document type `concepts_compact`.

The merged `docs/concepts.md` is the compact form of the concepts section. It
holds the concept register followed by one `##` section per domain concept the
manifest folded into it. Every discovered concept appears in the register
whether or not it has a section, so the vocabulary stays complete; the section
budget bounds how many are explained in full here. Each concept section carries
**every field** of the `concept` content contract, collapsing each repeated
block to one line per instance and keeping the contract's level order.
Condensed, never summarized: a folded concept that has lost its invariants or
its failure boundary is a defect.

| Type | Must present | Keep out | Primary mode | Depth |
|---|---|---|---|---|
| concepts_compact | section introduction, the concept register (concept, where it is defined in code, which documents depend on it), one section per folded concept carrying what it models, the block it belongs to, its lifecycle and states, its invariants stated as rules, how it relates to neighbouring concepts, its failure boundary, and where it lives; links to every selected, materialized document in this section's folder that this file does not merge | a concept with no definition in the repository, a term that is only a glossary entry, restating a rule an architecture section owns, a neighbouring concept's invariants, direct source-file navigation, a folded concept summarized rather than condensed | Explanation | deep-dive |
