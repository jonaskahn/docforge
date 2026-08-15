# `reference_compact`

Content contract for compact document type `reference_compact`.

The merged `docs/reference.md` is the compact form of the reference section.
At Spine it holds the section-level orientation (what a reader can look up
here) followed by configuration, limitations, and the technology stack. At
Diligence it additionally holds the glossary — one `##` section per member,
in reading order. Each section follows its member's own content contract;
the composed contract for this document lists the members this project's
manifest actually selected.

| Type | Must present | Keep out | Primary mode | Depth |
|---|---|---|---|---|
| reference_compact | section introduction, at-a-glance reference coverage, scope and boundaries, configuration reference, limitations register, technology stack; at Diligence also: the repository glossary | facts a member contract keeps out, lookup subjects this section does not own, direct source-file navigation, a glossary entry that restates a definition owned elsewhere instead of linking | Reference | reference |
