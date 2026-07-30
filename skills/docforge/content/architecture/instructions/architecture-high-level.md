# High-level architecture writing craft

**Preferred illustration:** Use the form and depth budget in
[`../../../references/illustration.md`](../../../references/illustration.md); a small
Mermaid flowchart suits context and container relationships.

Map onto C4's top two levels: "System in context" is the Context diagram (this system as
one box among the neighbors and services it borders); "Building blocks" is the Container
diagram (the deployable pieces inside that box). Keep the zoom consistent within each
section — don't let a container-level block sprout component-level detail; that belongs in
low-level.md.

Open with a one-paragraph system frame: what this is, at the highest level, and the
business capability it owns. Move from context to blocks to communication and boundaries in
that order — a reader should be able to draw the box diagram from the prose alone. Add a
visual only when it clarifies relationships among three or more blocks. Name responsibilities with
strong verbs ("owns," "validates," "routes"), not passive nouns ("handling,"
"management"). Put invariants in a visually distinct section — a reader skimming for "what
must always be true" should not have to parse prose to find it. This document is stable by
design: a claim a routine refactor would falsify is written too close to the code and
belongs in low-level.md. Finish with links to low-level detail, decisions, and operational
consequences — rationale lives in decisions, not here.
