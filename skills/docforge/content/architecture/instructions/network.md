# Network writing craft

**Preferred illustration:** Follow
[`../../../references/illustration.md`](../../../references/illustration.md); a
Mermaid flowchart for trust zones and the traffic crossing them — not a
full firewall-rule dump.

Draw trust zones first — public, internal, restricted — before any single
rule; a reader needs the zone map before a rule means anything. For each
boundary crossing, state what traffic crosses it and why, not every open
port; a rule with no stated purpose is noise a security reviewer has to
re-derive. Name the enforcement mechanism per boundary (security group,
network policy, firewall rule set) so a reader knows where to go verify
the current state, since network configuration drifts fast and this
document is prose, not the source of truth.

State what would happen if a boundary were removed — the concentration-risk
question dependencies-inventory.md asks about packages, asked here about
network segmentation.
