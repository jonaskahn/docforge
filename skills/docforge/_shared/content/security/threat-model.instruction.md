# Threat-model writing craft

For every control and response, cite code, configuration, or test evidence and
name an accountable owner only when established. Record accepted risk only with
a documented decision, rationale, review condition, and owner; otherwise leave
the exposure unresolved rather than describing it as mitigated.

**Preferred illustration:** Follow
[`../../references/illustration.md`](../../references/illustration.md); a data-flow
Mermaid diagram naming trust boundaries, prose for each threat and its
response.

Analyze a bounded DFD proportionately: name assets, trust zones, external
entities, processes, data stores, and flows first. Apply STRIDE (Spoofing,
Tampering, Repudiation, Information disclosure, Denial of service, Elevation
of privilege) to every bounded element using the canonical applicability map.
Each applicable matrix cell is `N/A`, `examined-none-found`, or a threat ID.

For each threat, give exactly one response — mitigate, eliminate, transfer,
or accept — tied to a control a reader could actually test.
An accepted risk needs a decision link, rationale, review condition, and
evidenced owner. `None accepted based on available evidence` is valid. Link
data classifications to [data-handling.md](data-handling.md) rather than
restating them — this document owns threats and responses, not the data
inventory. Keep disclosure workflow, credentials, and unremediated
vulnerability detail out entirely; the former belongs in
[security-policy.md](security-policy.md), the latter is not safe to
publish.

Scores and exhaustive interactions belong in the conditional `threat-register`
owner, never this narrative. Do not infer likelihood, owner, or control
effectiveness. Trust boundaries are zones or crossings, not process nodes.
