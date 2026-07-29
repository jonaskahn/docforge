# Publishing writing craft

**Preferred illustration:** Follow
[`../references/illustration.md`](../references/illustration.md); this is a
how-to — ordered commands and verification, not prose explanation.

One verified path: artifact, version source (where the version number
actually comes from — a file, a tag, a generator), build and sign,
registry or channel, verify, rollback or deprecate — in that order. Follow
each step with its observable success signal, the same discipline
setup-guide.md uses; a publish step with no verification is the step that
silently fails under pressure.

Give deprecation and rollback the same rigor as the happy path — a
publishing document that stops at "and now it's published" leaves the
reader with no way back. Never include a secret value (registry token,
signing key); name the mechanism, never the value. Keep changelog content
out — this document is the mechanics of publishing, not the record of what
was published.
