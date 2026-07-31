# Platform-permissions writing craft

Pair each manifest or entitlement declaration with source evidence for request
timing, denial fallback, and revocation recovery. Cite durable paths and relevant
declarations, not line numbers; a declaration without runtime evidence is a gap,
not proof of behavior.

**Preferred illustration:** Follow
[`../../references/illustration.md`](../../references/illustration.md); a table
per permission is primary, prose only for a denial-flow nuance.

One entry per requested capability, in this order: the capability itself,
what triggers the request (first launch, first use of a feature, explicit
settings action), the user-visible value it unlocks, and what happens if
the user denies it — least-privilege framing means a denial is an expected,
handled path, not an edge case. State how a user changes their mind later
(settings path) and what the app does when a previously granted permission
is revoked mid-session; a permission that silently breaks on revocation is
a defect this document should surface, not hide.

Ground every entry in the manifest, entitlement file, or platform
declaration that actually requests it — cite the evidence. Never invent an
entitlement, capability, or policy claim the repository does not evidence;
a permission the reader cannot find declared anywhere is worse than an
undocumented one, because it reads as authoritative.
