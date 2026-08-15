# `architecture_compact`

Content contract for compact document type `architecture_compact`.

The merged `docs/architecture.md` is the compact form of the architecture
section: the section-level orientation (system mental model, scope and
boundaries) followed by the high-level architecture, one `##` section per
member below. Each section follows its member's own content contract; the
composed contract for this document lists them in reading order.

| Type | Must present | Keep out | Primary mode | Depth |
|---|---|---|---|---|
| architecture_compact | section introduction, at-a-glance system mental model, scope and boundaries, high-level architecture (structure, boundaries, integration surfaces) | component-level detail a member contract reserves for its own document, invented architecture not grounded in source, direct source-file navigation | Orientation | orientation |
