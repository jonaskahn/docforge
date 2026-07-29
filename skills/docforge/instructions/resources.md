# Resources / access writing craft

Covers `infra_resources` and `infra_access` — both are lookup inventories;
the craft is keeping them that way rather than letting narrative creep in.

**Preferred illustration:** Follow
[`../references/illustration.md`](../references/illustration.md); tables
only — this is Reference depth, not Explanation.

Resources: one row per managed resource — name, type, owner, criticality.
Order by criticality, the same principle dependencies-inventory.md uses,
not alphabetically. Access: one row per grant — principal, scope, how the
grant was made (path, not just "IAM"), and review cadence if one exists. A
grant with no review cadence stated reads as permanent by default; say so
if that's true rather than leaving it silent.

Never include a credential, secret, or literal access key — name the
mechanism (a role, a policy, a secret manager reference), never the
value.
