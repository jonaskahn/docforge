# Data-types writing craft

**Preferred illustration:** Follow
[`../../../references/illustration.md`](../../../references/illustration.md); a single
table is almost always sufficient — this document is a lookup, not an
explanation.

One row per type: name, wire representation (not the internal language
type), constraints (range, length, pattern), and nullability. State the
wire representation precisely enough to implement against — "timestamp"
is not a wire representation, "ISO 8601 string, UTC" is. Where a type has
been renamed or its representation changed, note the prior representation
and the version it changed in; a silent representation change is the kind
of thing that breaks callers without a compiler error.

Order types by how often a reader looks them up — the types used across
the most operations first — not alphabetically and not by internal module.
Do not restate business meaning already owned by
[business-rules.md](business-rules.md) or [glossary.md](glossary.md); this
document owns representation, not meaning.
