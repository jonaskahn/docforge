# Contract-system writing craft

Open with the contract inventory: which on-chain contracts exist and the
one responsibility each owns. Trace storage next (what state each contract
persists on-chain and why), authorities (which accounts/roles can call
privileged functions and under what condition), and networks (which chains
or environments this deploys to and how they differ). State the upgrade
boundary explicitly — what can change after deployment, what is immutable,
and the mechanism (proxy, migration, governance vote) that gates a change.
Close with the economic and security invariants: properties that must hold
for the system to be solvent and safe, stated as things that must always be
true, not as a description of the current implementation.

Never present an unsupported audit verdict — state only what this document's
own evidence (code, deployment records, governance history) actually
supports; a security claim without that backing belongs in a real audit
report, not asserted here.

## Illustration

- **Form:** a Mermaid `flowchart` for authority/call relationships between
  contracts; a table for the per-contract storage/authority inventory.
- **Renders:** which account or contract can call which privileged function
  on which target, and the storage each contract owns.
- **Trigger:** the flowchart only once three or more contracts have
  authority relationships worth tracing together — per
  [`illustration.md`](../../../references/illustration.md)'s deep-dive
  budget.

## Connections

| This document owns | Links to | Because |
|---|---|---|
| Contracts, storage, authorities, networks, upgrade boundary, economic/security invariants | `security/threat-model` | the threat model analyzes attack surfaces against these invariants; it does not restate the inventory |
| An accepted risk in the upgrade path | `security/threat-model`'s accepted-risk section | never restate an accepted risk as if it were a hard invariant here |
| A deliberate immutability choice | `constraints` | a chosen, immovable design bound belongs there if it is non-negotiable by design |
