# Network writing craft

- Name the infrastructure or network-policy source of truth for every zone
  crossing and enforcement boundary.
- Mark unverified topology and removal-impact claims as unknown rather than
  treating a configuration snapshot as current reality.
- Draw trust zones first — public, internal, restricted — before any single
  rule.
- For each boundary crossing, state what traffic crosses it and why, not
  every open port.
- Name the enforcement mechanism per boundary (security group, network
  policy, firewall rule set) so a reader knows where to go verify the
  current state.
- State what would happen if a boundary were removed — the
  concentration-risk question `dependencies-inventory` asks about packages,
  asked here about network segmentation.

## Illustration

- **Form:** a Mermaid `flowchart` for trust zones and the traffic crossing
  them — not a full firewall-rule dump.
- **Renders:** each zone as a node and each crossing as a labeled edge
  stating its purpose.
- **Trigger:** always for this document type — zone relationships are the
  point — within
  [`illustration.md`](../../../references/illustration.md)'s deep-dive budget.

## Connections

| This document owns | Links to | Because |
|---|---|---|
| Topology zones, boundary crossings, traffic purpose, enforcement, concentration-risk | `security/threat-model` | the threat model analyzes what an attacker gains per boundary; this document only maps the zones and crossings |
| A dependency whose failure exposes a network boundary | `dependencies-inventory` | asks the same concentration-risk question about packages; link rather than re-derive |
| Credential material referenced by an enforcement mechanism | never this document | credential material is explicitly kept out; link to a secrets-management reference if one exists |

## Voice

- **Voice:** declarative present tense, strong active verbs, no hedging.
