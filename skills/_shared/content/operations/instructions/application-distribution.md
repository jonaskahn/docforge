# Application-distribution writing craft

**Preferred illustration:** Follow
[`../../../references/illustration.md`](../../../references/illustration.md); this is a
how-to — ordered steps and verification, not a diagram.

One verified path from artifact to installed application: build, sign,
package, publish to channel, verify — in that order, since signing before
packaging or packaging before signing are not interchangeable and a reader
following the wrong order produces an unusable artifact. Name every channel
in use (store, direct download, internal distribution) and what differs
about the procedure per channel, rather than one generic description that
quietly only covers one.

Give update and rollback the same rigor as initial publish — a distribution
document that stops at "and now it's live" leaves the reader with no way
back. Never include a signing key, secret, or unverified claim about store
approval timelines the repository doesn't evidence.
