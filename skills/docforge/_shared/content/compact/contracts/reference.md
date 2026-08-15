# `reference_compact`

Content contract for compact document type `reference_compact`.

The merged `docs/reference.md` is the compact form of the reference section:
the section-level orientation (what a reader can look up here) followed by
configuration, limitations, and the technology stack, one `##` section per
member below. Each section follows its member's own content contract; the
composed contract for this document lists them in reading order.

| Type | Must present | Keep out | Primary mode | Depth |
|---|---|---|---|---|
| reference_compact | section introduction, at-a-glance reference coverage, scope and boundaries, configuration reference, limitations register, technology stack | facts a member contract keeps out, lookup subjects this section does not own, direct source-file navigation | Reference | reference |
