# Api-versioning writing craft

For every public deprecation, link the evidenced migration path or state that
none is published. Ground compatibility and removal claims in current public
contracts and history; never promise an unverified future version or date.

**Preferred illustration:** Follow
[`../../../references/illustration.md`](../../../references/illustration.md); a compact
table for the version/date/status facts, prose for the compatibility
promise itself.

State the versioning scheme first, in one sentence a caller can act on:
what changes without a version bump (additive fields, new optional
parameters) and what forces one (removed fields, changed types, changed
error semantics). Name how a caller pins a version (header, path segment,
or account default) before describing what changes between versions.

Give every deprecation the same three facts, in the same order: the version
it was deprecated in, the version (or date) it will stop working, and the
replacement to migrate to. State "not yet scheduled" plainly rather than
omitting the removal date. Order deprecations by how soon they bite, not
alphabetically. Link the operation-level detail to
[api-reference.md](api-reference.md) rather than repeating request/response
shapes here — this document owns the compatibility promise, not the
surface.
