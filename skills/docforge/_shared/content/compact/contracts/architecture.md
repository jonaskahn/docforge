# `architecture_compact`

Content contract for compact document type `architecture_compact`.

The merged `docs/architecture.md` is the compact form of the architecture
section. At Spine it holds the section-level orientation (system mental
model, scope and boundaries) followed by the high-level architecture. At
Diligence it additionally holds the whitebox decomposition, hard constraints,
the dependency inventory, and the tech-debt register — one `##` section per
member, in reading order. Each section follows its member's own content
contract; the composed contract for this document lists the members this
project's manifest actually selected.

| Type | Must present | Keep out | Primary mode | Depth |
|---|---|---|---|---|
| architecture_compact | section introduction, at-a-glance system mental model, scope and boundaries, high-level architecture (structure, boundaries, integration surfaces); at Diligence also: whitebox decomposition and one intra-block runtime scenario, hard constraints with design implication, the dependency inventory, and the tech-debt register; links to every selected, materialized document in this section's folder that this file does not merge | component-level detail a member contract reserves for its own document, invented architecture not grounded in source, direct source-file navigation, duplicated high-level map inside the low-level section, user-visible limitations inside tech-debt, hard constraints inside tech-debt | Orientation (Explanation/Reference in the Diligence sections) | orientation |
