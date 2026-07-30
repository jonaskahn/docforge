# Release-guide writing craft

**Preferred illustration:** Follow
[`../../../references/illustration.md`](../../../references/illustration.md); this is a
how-to (Diataxis) — ordered commands and verification, not prose
explanation.

One verified path: prerequisites, version bump (state the scheme —
SemVer or equivalent — and what triggers major versus minor versus patch),
build, verification, publication, rollback — in that order. Follow each
command with its observable success signal, the same discipline
setup-guide.md uses; a release step with no way to confirm it worked is
the step that gets skipped under pressure.

Give rollback equal weight to publication, not an afterthought paragraph
at the end. Keep changelog content out — this document is the procedure to
release, [changelog.md](changelog.md) is the record of what was released.
