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

## Illustration

- **Form:** prose and a credential table; a Mermaid `sequenceDiagram` only
  when a flow (OAuth2 authorization code, mTLS handshake) has more than two
  actors.
- **Renders:** per scheme, the credential lifecycle — issued, transmitted,
  rotated, then expiry/revocation; for multi-actor flows, the actors and
  each call in order.
- **Trigger:** only when a flow has more than two actors — otherwise prose
  and the credential table, per
  [`../../references/illustration.md`](../../references/illustration.md).

## Connections

| This document owns | Links to | Because |
|---|---|---|
| The public surface and compatibility boundary | `api-reference` | the schema or generator that defines it is owned there |
| Quota contracts | `api-rate-limits` | owned there, linked not restated |
| Shared error contracts | `api-errors` | owned there, linked not restated |

## Voice

- **Voice:** precise; hedge only where evidence is thin; never alarmist.

## Data-handling writing craft

For each data-class lifecycle row, cite repository evidence for collection, use,
access, storage or retention, and deletion. Keep classification here, but link
retention authority and deletion execution to their evidence-backed owner; state
unevidenced duration, processor, or outcome as a limit.

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

## Illustration

- **Form:** a Markdown table for data class × lifecycle stage; prose only
  for a nuance a table cannot carry.
- **Renders:** per class — collection, use, retention, deletion, access
  boundaries.
- **Trigger:** never — the table plus prose, per
  [`../../references/illustration.md`](../../references/illustration.md).

## Connections

| This document owns | Links to | Because |
|---|---|---|
| Data classes, lifecycle, access boundaries, deletion | `threat-model` | classifications are referenced there, never restated |
| The security contact role or channel | `security-policy` | owned there, referenced not restated |

## Voice

- **Voice:** precise; hedge only where evidence is thin; never alarmist.

## Platform-permissions writing craft

Pair each manifest or entitlement declaration with provenance for request timing,
denial fallback, and revocation recovery. A declaration without runtime evidence
is a gap, not proof of behavior.

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

## Illustration

- **Form:** a Markdown table per permission; prose only for a denial-flow
  nuance.
- **Renders:** capability, request trigger, value unlocked, denial behavior,
  revocation recovery.
- **Trigger:** never — the permission table is primary, per
  [`../../references/illustration.md`](../../references/illustration.md).

## Connections

| This document owns | Links to | Because |
|---|---|---|
| Requested capabilities, request timing, denial fallback, revocation recovery | `platform-compatibility` | platform minimums and degradation are owned there |
| The data a granted permission unlocks | `data-handling` | access boundaries per class are owned there |

## Voice

- **Voice:** precise; hedge only where evidence is thin; never alarmist.

## Security-policy writing craft

Add a distinct Safe harbor and authorized testing section only when an accountable
policy decision establishes it, including good-faith limits and exclusions. Cite
policy, release, configuration, or maintainer evidence for scope, contact, and
response commitments; otherwise retain typed external unknowns.

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

## Illustration

- **Form:** procedural prose; a diagram only when an evidenced lifecycle
  needs three or more states.
- **Renders:** scope, reporting steps, response commitments — the facts a
  reporter acts on without guessing.
- **Trigger:** only when an evidenced lifecycle needs three or more states —
  disclosure policy is procedural prose, per
  [`../../references/illustration.md`](../../references/illustration.md).

## Connections

| This document owns | Links to | Because |
|---|---|---|
| Scope, reporting procedure, response commitments, safe harbor | `threat-model` | technical analysis is owned there; this page is procedure, not analysis |
| Scored threats and exhaustive interactions | `threat-register` | owned there, never restated on this page |

## Voice

- **Voice:** precise; hedge only where evidence is thin; never alarmist.

## Threat-model writing craft

For every control and response, cite code, configuration, or test evidence and
name an accountable owner only when established. Record accepted risk only with
a documented decision, rationale, review condition, and owner; otherwise leave
the exposure unresolved rather than describing it as mitigated.

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

## Illustration

- **Form:** a data-flow Mermaid diagram naming trust boundaries; prose for
  each threat and its response.
- **Renders:** assets, trust zones, external entities, processes, data
  stores, and flows — then one response per threat tied to a testable
  control.
- **Trigger:** the bounded DFD is the analysis frame — draw it before the
  STRIDE pass, per
  [`../../references/illustration.md`](../../references/illustration.md).

## Connections

| This document owns | Links to | Because |
|---|---|---|
| The bounded DFD, STRIDE matrix, threats, responses | `threat-register` | scores and exhaustive interactions are owned there, never this narrative |
| Data classifications | `data-handling` | owned there, linked not restated |
| Disclosure workflow | `security-policy` | owned there; kept out of this document |

## Voice

- **Voice:** precise; hedge only where evidence is thin; never alarmist.

## Threat-register writing craft

Generate this dynamic document only after a recorded high-criticality trigger
and security-reviewer audience selection. Use one qualitative Likelihood x
Impact rubric throughout, or `unscored` if evidence cannot support a score.
Each row covers one STRIDE category for one named DFD interaction. Controls must
be concrete and safe to publish; name an owner only when evidence establishes
one. Link back to `threat-model` for the bounded DFD and narrative.

## Illustration

- **Form:** a Markdown table — one row per threat.
- **Renders:** one STRIDE category per named DFD interaction, with
  likelihood, impact, control, and owner.
- **Trigger:** never — the bounded DFD and narrative are owned by
  `threat-model`, linked not redrawn.

## Connections

| This document owns | Links to | Because |
|---|---|---|
| Scored threats, controls, owners | `threat-model` | the bounded DFD and narrative this register scores are owned there |

## Voice

- **Voice:** precise; hedge only where evidence is thin; never alarmist.
