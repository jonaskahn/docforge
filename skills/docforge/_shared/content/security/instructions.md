# Security writing craft

Writing-craft instructions for `security` group documents. Routes:

- `api_authentication` → [Api-authentication](#api-authentication-writing-craft)
- `data_handling` → [Data-handling](#data-handling-writing-craft)
- `platform_permissions` → [Platform-permissions](#platform-permissions-writing-craft)
- `security_root` → [Security-policy](#security-policy-writing-craft)
- `threat_model` → [Threat-model](#threat-model-writing-craft)
- `threat_register` → [Threat-register](#threat-register-writing-craft)

## Api-authentication writing craft

Open with the authoritative schema, export, or generator that defines the public
surface and compatibility boundary. Ground issuance, rotation, revocation,
scopes, statuses, and caller actions in code, config, or schema evidence; link
quota and shared error contracts to their reference owners.

**Preferred illustration:** Follow
[`../../references/illustration.md`](../../references/illustration.md); a
sequence diagram only when a flow (OAuth2 authorization code, mTLS
handshake) has more than two actors — otherwise prose and a credential
table.

Name the scheme by its real category first — API key, bearer token, OAuth2
grant type, mTLS, signed request. For each scheme in use, state the
credential's lifecycle in order: issued, transmitted, rotated, then what
happens when it expires or is revoked.

Give a failure-mode table, not scattered prose: missing credential, expired
credential, revoked credential, wrong scope — each with its status code and
what the caller should do next. State scope or permission boundaries as
data (a table of scope → capability), not as a paragraph the caller must
parse to find the one scope they need. Never include a real credential,
secret, or token value, including as an "example" — use an obviously
synthetic placeholder.

## Data-handling writing craft

For each data-class lifecycle row, cite repository evidence for collection, use,
access, storage or retention, and deletion. Keep classification here, but link
retention authority and deletion execution to their evidence-backed owner; state
unevidenced duration, processor, or outcome as a limit.

**Preferred illustration:** Follow
[`../../references/illustration.md`](../../references/illustration.md); a table
for data class × lifecycle stage, prose only for a nuance a table cannot
carry.

Classify data first — the categories the system actually distinguishes
(public, internal, confidential, regulated/PII), not a generic three-tier
scheme borrowed from a compliance template. For each class, state the full
lifecycle in order: how collected, where used, how long retained and why
that duration, and how deletion actually happens (mechanism, not policy
language). A retention period with no deletion mechanism behind it is a
promise this document cannot back up.

State access boundaries per class — who or what can read it, not "access is
controlled." Never assert a compliance posture (GDPR, HIPAA, SOC 2) the
repository has not evidenced; an invented compliance claim is worse than no
claim. Never name an internal hostname, a real credential, or an
individual's name as a security contact — use the role or the channel from
[Security-policy](#security-policy-writing-craft) instead.

## Platform-permissions writing craft

Pair each manifest or entitlement declaration with provenance for request timing,
denial fallback, and revocation recovery. A declaration without runtime evidence
is a gap, not proof of behavior.

**Preferred illustration:** Follow
[`../../references/illustration.md`](../../references/illustration.md); a table
per permission is primary, prose only for a denial-flow nuance.

One entry per requested capability, in this order: the capability itself,
what triggers the request (first launch, first use of a feature, explicit
settings action), the user-visible value it unlocks, and what happens if
the user denies it. State how a user changes their mind later (settings
path) and what the app does when a previously granted permission is
revoked mid-session; a permission that silently breaks on revocation is a
defect this document should surface, not hide.

Ground every entry in the manifest, entitlement file, or platform declaration
that actually requests it. Never invent an entitlement, capability, or policy
claim the repository does not evidence; a permission the reader cannot find
declared anywhere is worse than an undocumented one, because it reads as
authoritative.

## Security-policy writing craft

Add a distinct Safe harbor and authorized testing section only when an accountable
policy decision establishes it, including good-faith limits and exclusions. Cite
policy, release, configuration, or maintainer evidence for scope, contact, and
response commitments; otherwise retain typed external unknowns.

**Preferred illustration:** Follow
[`../../references/illustration.md`](../../references/illustration.md); disclosure
policy is procedural prose, not a diagram, unless an evidenced lifecycle needs
three or more states.

Write disclosure instructions as a calm, unambiguous procedure — the human-readable
companion to a `security.txt` (RFC 9116): the same facts a machine-readable Contact and
Policy field point to, in prose a reporter can act on without guessing. Where the project
publishes `security.txt`, require at least Contact and Expires; Policy and Encryption are
optional pointers to this same page.

Put supported scope before reporting steps: state which versions or components are in
scope and, just as plainly, what testing is not authorized (no destructive testing, no
data exfiltration, no social engineering). Use
typed tokens only for external contact, response-time, and disclosure-window values; never
invent a number, an address, or a timeline that has not been confirmed. Commit only to an
acknowledgement window the project can actually meet;
ninety days is the common coordinated-disclosure default when no
confirmed window exists yet. State any safe-harbor commitment explicitly and
unconditionally where it applies, in the spirit of the DOJ's 2022 good-faith-research
guidance.
Distinguish what reporters should include (reproduction steps, impact, affected version)
from what they must not do, as two short, separate lists, not one merged paragraph. Keep
technical threat-model detail in the linked security documents; this page is a procedure,
not an analysis.

## Threat-model writing craft

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
data classifications to [Data-handling](#data-handling-writing-craft) rather than
restating them — this document owns threats and responses, not the data
inventory. Keep disclosure workflow, credentials, and unremediated
vulnerability detail out entirely; the former belongs in
[Security-policy](#security-policy-writing-craft), the latter is not safe to
publish.

Scores and exhaustive interactions belong in the conditional `threat-register`
owner, never this narrative. Do not infer likelihood, owner, or control
effectiveness. Trust boundaries are zones or crossings, not process nodes.

## Threat-register writing craft

Generate this dynamic document only after a recorded high-criticality trigger
and security-reviewer audience selection. Use one qualitative Likelihood x
Impact rubric throughout, or `unscored` if evidence cannot support a score.
Each row covers one STRIDE category for one named DFD interaction. Controls must
be concrete and safe to publish; name an owner only when evidence establishes
one. Link back to `threat-model` for the bounded DFD and narrative.
