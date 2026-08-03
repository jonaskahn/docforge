# Publishing writing craft

Before publishing, name artifact identity, version-tag consistency, required
build/test/approval gates, and the non-secret credential mechanism from
manifests, CI, and history. State the evidenced bad-release branch
(unpublish/yank, deprecate, or patch) and link the catalog-selected changelog.

**Preferred illustration:** Follow
[`../../../references/illustration.md`](../../../references/illustration.md); this is a
how-to — ordered commands and verification, not prose explanation.

One verified path: artifact, version source (where the version number
actually comes from — a file, a tag, a generator), build and sign,
registry or channel, verify, rollback or deprecate — in that order. Follow
each step with its observable success signal, the same discipline
setup-guide.md uses.

Give deprecation and rollback the same rigor as the happy path. Never
include a secret value (registry token, signing key); name the mechanism,
never the value. Keep changelog content
out — this document is the mechanics of publishing, not the record of what
was published.
