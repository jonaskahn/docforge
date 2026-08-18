# Contract-system / economic-invariants writing craft

Covers both `contract_system` and `economic_invariants` — profile-gated to
repositories with on-chain contracts. Grounded in the trust-boundary and
invariant framing used by manual smart-contract audits (Trail of Bits,
ConsenSys Diligence style): map the system boundary and trust assumptions
before individual mechanisms, then state what must always hold.

- For contract-system: name every contract, its storage layout at the level
  a reader needs (not a field-by-field dump), which authorities can call its
  privileged functions, which network(s) it is deployed to, and its upgrade
  boundary — immutable, proxy-upgradeable, or governance-gated — stated
  plainly.
- For economic-invariants: state each invariant as a fact that must always
  hold ("total minted never exceeds total collateral locked"), then what
  mechanism enforces it and what would have to fail for it to break.
- Never render an unsupported audit verdict ("this contract is safe"); state
  evidence and accepted residual risk instead, the same discipline
  `threat-model` uses. Never include a private key or a fabricated address —
  placeholders only.
- Keep the paired views distinct: `contract_system` owns the contract,
  network, storage, authority, and upgrade inventory; `economic_invariants`
  owns each invariant, enforcement mechanism, break condition, and evidence
  status. Link from inventory rows to invariant identifiers rather than
  restating them, and link accepted risks to the threat model.
- Network, authority, upgrade, and governance claims require deployment or
  governance evidence; absent evidence is an explicit unknown, never a
  safety conclusion.

## Illustration

- **Form:** tables and prose; a Mermaid `erDiagram` or `flowchart` only for
  contract-to-contract call relationships that prose cannot carry cleanly.
- **Renders:** the call relationships among contracts — otherwise the
  inventory tables and invariant statements themselves.
- **Trigger:** only when contract-to-contract call relationships cannot be
  read as prose, per
  [`../../references/illustration.md`](../../references/illustration.md).

## Connections

| This document owns | Links to | Because |
|---|---|---|
| Invariant identifiers and their enforcement mechanisms | `economic-invariants` | the paired view; inventory rows link to invariants, never restate them |
| Accepted residual risk and audit evidence | `threat-model` | the same evidence-and-residual-risk discipline is owned there |

## Voice

- **Voice:** precise; hedge only where evidence is thin; never alarmist.
