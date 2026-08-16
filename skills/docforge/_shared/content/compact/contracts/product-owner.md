# `po_compact`

Content contract for compact document type `po_compact`.

The merged `docs/product-owner.md` is the compact form of the product-owner
views. It holds the section-level orientation followed by the feature
catalog, success metrics, and release notes — one `##` section per member, in
reading order. When the repository carries ticket evidence it additionally
holds backlog traceability. Each section follows its member's own content
contract; the composed contract for this document lists the members this
project's manifest actually selected.

| Type | Must present | Keep out | Primary mode | Depth |
|---|---|---|---|---|
| po_compact | section introduction, at-a-glance product shape, scope and boundaries, feature catalog (user outcome, audience, availability, owning flow), success metrics (outcome, measure, instrumentation state, interpretation, external target token), release notes (released user impact, version/date, compatibility impact, feature links); when ticket evidence exists also: backlog traceability (evidenced ticket id, feature, flow/change, release/status link) | implementation inventory, invented targets, guessed ticket mappings, empty seed tables, internal refactor and dependency noise, direct source-file navigation | Reference | deep-dive |
