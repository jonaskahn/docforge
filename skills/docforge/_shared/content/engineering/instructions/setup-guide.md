# Setup-guide writing craft

Ground every prerequisite, version, command, and success signal in manifests,
CI, or local verification. Record unavailable external access as a typed unknown
with its grantor; link configuration semantics and technology inventory to their
reference owners rather than recreating them here.

**Preferred illustration:** Follow
[`../../../references/illustration.md`](../../../references/illustration.md); use prose and
commands by default, with an ASCII timeline only when sequencing is otherwise
ambiguous.

This is a how-to, not a tutorial (Diataxis distinction): the reader already wants to run
the thing, not learn why it works. Write a single verified path from prerequisites to a
running instance — one path, not a menu of alternatives.

Use second person and the imperative, present tense, one command per step: "Run `X`," not
"You could run `X`" or "Running `X` will...". Follow each command immediately with the
observable success signal — the exact output or state a reader checks before moving on, not
a paragraph of explanation. Introduce configuration immediately before it is needed, not as
a wall of settings up front. Put common recovery steps beside the failure they fix, keyed by
the symptom the reader is looking at, not by cause. Finish with the smallest useful
verification and a short "what next."
