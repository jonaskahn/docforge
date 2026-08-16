# `engineering_compact`

Content contract for compact document type `engineering_compact`.

The merged `docs/engineering.md` is the compact form of the engineering
section. At Spine it holds the section-level orientation (how this
repository is built and tested) followed by the setup guide and the testing
guide. At Diligence it additionally holds evidenced conventions (when a
conventions source exists) and the release guide — one `##` section per
member, in reading order. Each section follows its member's own content
contract; the composed contract for this document lists the members this
project's manifest actually selected.

| Type | Must present | Keep out | Primary mode | Depth |
|---|---|---|---|---|
| engineering_compact | section introduction, at-a-glance engineering practices, scope and boundaries, setup instructions, testing instructions; at Diligence also: evidenced conventions when a conventions source exists, and the release procedure; links to every selected, materialized document in this section's folder that this file does not merge | commands or rules the member contracts keep out, generic style advice with no repository evidence, direct source-file navigation | Explanation | orientation |
