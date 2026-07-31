# Resources / access writing craft

Covers `infra_resources` and `infra_access` — both are lookup inventories;
the craft is keeping them that way rather than letting narrative creep in.

**Preferred illustration:** Follow
[`../../../references/illustration.md`](../../../references/illustration.md); tables
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

For each resource, include a stable locator or context (such as account,
environment, region, or canonical address) and a source-of-truth link; do not
copy mutable state or apply procedure. For access, distinguish an evidenced
review cadence from `unknown` rather than treating silence as permanence. Keep
resource inventory and grants separate: a resource does not prove who can use
it, and a grant does not prove current resource state.
