# Data-handling writing craft

**Preferred illustration:** Follow
[`../references/illustration.md`](../references/illustration.md); a table
for data class × lifecycle stage, prose only for a nuance a table cannot
carry.

Classify data first — the categories the system actually distinguishes
(public, internal, confidential, regulated/PII), not a generic three-tier
scheme borrowed from a compliance template. For each class, state the full
lifecycle in order: how it is collected, where it is used, how long it is
retained and why that duration, and how deletion actually happens
(mechanism, not policy language). A retention period with no deletion
mechanism behind it is a promise this document cannot back up.

State access boundaries per class — who or what can read it, not "access is
controlled." Never assert a compliance posture (GDPR, HIPAA, SOC 2) the
repository has not evidenced; an invented compliance claim is worse than no
claim. Never name an internal hostname, a real credential, or an
individual's name as a security contact — use the role or the channel from
[security-policy.md](security-policy.md) instead.
