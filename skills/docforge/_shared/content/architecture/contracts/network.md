# `network`

**Reader question** — "What trust zones exist, what crosses between them, and what happens if a boundary is removed?"

| Mode | Depth | Shape |
|---|---|---|
| Explanation | deep-dive | answer-first |

Trust zones are drawn first — public, internal, restricted — before any single boundary crossing.

## Must present

| # | Element | At | Done wrong |
|---|---|---|---|
| 1 | Trust zones, named before any single rule | L0 | a firewall-rule dump instead of the zone model |
| 2 | Per boundary crossing: what traffic crosses it and why | L1 | every open port listed instead of the crossings that matter |
| 3 | The enforcement mechanism per boundary (security group, network policy, firewall rule set) | L2 | an enforcement mechanism left unnamed, with no pointer to verify current state |
| 4 | Concentration risk: what would happen if a boundary were removed | L2 | an unverified topology or removal-impact claim treated as current reality |

## Keep out

| Not here | Lives in |
|---|---|
| A full firewall-rule dump | nowhere |
| Credential material | nowhere — never in this document |
| What an attacker gains per boundary | `threat_model` |

## Owns / links

| Owns | Links to | Because |
|---|---|---|
| Topology zones, boundary crossings, traffic purpose, enforcement, concentration-risk | `threat_model` | the threat model analyzes what an attacker gains per boundary; this document only maps the zones and crossings |
| A dependency whose failure exposes a network boundary | `dependencies` | asks the same concentration-risk question about packages; link rather than re-derive |
