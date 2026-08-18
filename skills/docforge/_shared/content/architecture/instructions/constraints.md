# Constraints writing craft

- State each hard bound as a fact with a source and a consequence: what
  imposes it (a platform limit, a regulation, a third-party contract,
  physics), and what it forces the design to do or avoid. A constraint
  without a traceable source reads as an opinion, not a bound a reviewer can
  verify.
- Group deliberate non-goals separately from imposed bounds — a non-goal is a
  choice this team made and could unmake; a constraint is not.
- This document is the one place hard, externally imposed, immovable bounds
  live. Do not let a fixable shortcut drift in here disguised as a
  constraint, and do not let a user-visible accepted limitation hide here
  instead of in `limitations-register`.

## Illustration

- **Form:** a Markdown table — source, bound, consequence — over prose or a
  diagram; a constraint is a lookup fact, not a relationship.
- **Renders:** nothing beyond the table; add prose only where a single bound
  needs more than one sentence of consequence.
- **Trigger:** never for a diagram — reference-adjacent lookup content per
  [`illustration.md`](../../../references/illustration.md).

## Connections

| This document owns | Links to | Because |
|---|---|---|
| Hard, externally imposed, immovable bounds | `tech-debt-register` | fixable-by-us shortcuts are routed there instead, never cross-filed |
| — | `limitations-register` | deliberate, accepted, user-visible limitations are routed there instead, never cross-filed |
| A bound that shapes a specific block | `architecture-high-level` (the affected block) | the block names what it is; this document says why it cannot be otherwise |

## Voice

- **Voice:** declarative present tense, strong active verbs, no hedging.
