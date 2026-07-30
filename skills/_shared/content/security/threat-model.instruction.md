# Threat-model writing craft

**Preferred illustration:** Follow
[`../../references/illustration.md`](../../references/illustration.md); a data-flow
Mermaid diagram naming trust boundaries, prose for each threat and its
response.

Analyze proportionately, per [`../README.md`](../README.md)'s risk-register routing:
a trust-boundary data-flow diagram, STRIDE (Spoofing, Tampering,
Repudiation, Information disclosure, Denial of service, Elevation of
privilege) applied per element that crosses a boundary — not every element
in the system. Name assets and trust boundaries first, before any threat;
a threat without a named boundary it crosses is unfalsifiable.

For each threat, give exactly one response — mitigate, eliminate, transfer,
or accept — tied to a control a reader could actually test, not a hope.
Give the accepted-risk section real content: this is the reviewer's signal
that analysis happened, not a formality. An empty accepted-risk section on
a nontrivial system reads as an incomplete review, not a clean one. Link
data classifications to [data-handling.md](data-handling.md) rather than
restating them — this document owns threats and responses, not the data
inventory. Keep disclosure workflow, credentials, and unremediated
vulnerability detail out entirely; the former belongs in
[security-policy.md](security-policy.md), the latter is not safe to
publish.
