# `concepts_compact`

Content contract for compact document type `concepts_compact`.

The merged `docs/concepts.md` is the compact form of the concepts section. It
holds the concept register followed by one `##` section per domain concept the
manifest folded into it. Every discovered concept appears in the register
whether or not it has a section, so the vocabulary stays complete; the section
budget bounds how many are explained in full here. Each concept section
follows the `concept` content contract.

| Type | Must present | Keep out | Primary mode | Depth |
|---|---|---|---|---|
| concepts_compact | section introduction, the concept register (concept, where it is defined in code, which documents depend on it), one section per folded concept carrying what it models, its lifecycle and states, its invariants, and how it relates to neighbouring concepts; links to every selected, materialized document in this section's folder that this file does not merge | a concept with no definition in the repository, a term that is only a glossary entry, restating a rule an architecture section owns, direct source-file navigation | Explanation | deep-dive |
