# `security_compact`

**Reader question** — "What are this system's assets and threats, and what has actually been verified?"

| Mode | Depth | Shape |
|---|---|---|
| Explanation | orientation | merged-section-spine |

## What this file merges

| Member | At |
|---|---|
| `security_index` | diligence |
| `threat_model` | diligence |
| `data_handling` | diligence |
| `api_authentication` | spine + api-service |
| `economic_invariants` | spine + smart-contract |
| `platform_permissions` | spine + mobile-app, desktop-app |
| `threat_register` | diligence + security-reviewers (`discovered_high_criticality`) |

## Must present

| # | Element | At | Done wrong |
|---|---|---|---|
| 1 | Section introduction: what this section covers and who should read it | lead | a disclosure workflow instead of a posture summary |
| 2 | At-a-glance security posture | `## At a glance` | detail a member section owns |
| 3 | Scope and boundaries, linking every unmerged document in this folder | `## Scope and boundaries` | a link to an unmaterialized path |
| 4 | A bounded DFD with zones and a full element-by-STRIDE matrix | `## Threat model` | disclosure workflow or credentials appearing anywhere in this file |
| 5 | Concrete threats, each with exactly one disposition | `## Threat model` | a threat left with no disposition |
| 6 | Data classes with lifecycle, access, retention, and deletion | `## Data handling` | an invented compliance claim with no evidence |
| 7 | Every field of each folded member's own contract, condensed never summarized | `## {{Member}}` | a guessed score or owner in place of `unscored` / `unowned` |

## Keep out

| Not here | Lives in |
|---|---|
| Disclosure workflow or credentials | `root_security` (SECURITY.md) |
| An individual's name as a security contact | nowhere — use a role or channel |
| Invented compliance claims | nowhere — cite the control or omit the claim |
| Direct source-file navigation | provenance |

## Owns / links

| Owns | Links to | Because |
|---|---|---|
| Section introduction, at-a-glance posture, scope, and every folded member's content | every unmerged document in `docs/security/` | the fold covers the tier-selected members only; the rest keep their own paths |
| Nothing a folded member owns beyond hosting it | `security.md#<section anchor>` | a folded member has no file of its own; its contract's own links resolve inside this file |
