# Host-integration writing craft

Open with the host contract: which host product this integrates with and
the version/API surface it targets. Trace activation next (what causes the
host to load this integration), then contribution points (what it adds to
the host — commands, panels, hooks, extension slots), permissions (what the
host grants it access to and what it must declare to get that access),
compatibility (which host versions are supported and how that is verified),
and sandbox behavior (what the host isolates it from and what crossing that
isolation requires). Close with failure behavior — what happens if
activation fails, if a contribution point throws, or if the host revokes a
permission mid-session.

This is not a tutorial for using the host product; assume the reader already
knows the host and needs only this integration's contract with it.

## Illustration

- **Form:** a Mermaid `sequenceDiagram` for activation and the
  host-to-integration call order; a table for the contribution-point
  inventory.
- **Renders:** the handshake between host and integration at activation, and
  a lookup of what each contribution point does and what permission it
  needs.
- **Trigger:** the sequence diagram once activation involves more than a
  single call — per
  [`illustration.md`](../../../references/illustration.md)'s deep-dive
  budget (at most 5 participants).

## Connections

| This document owns | Links to | Because |
|---|---|---|
| Host contract, activation, contribution points, permissions, compatibility, sandbox, failure | `platform-integration` | platform-integration owns the OS/runtime surface; this document owns the host-product surface — do not merge the two |
| A permission also covered by the security posture | `security/platform-permissions` (or equivalent) | permission scope is a security-owned fact; this document names which are requested, not the security rationale |
| A compatibility bound the host imposes | `constraints` | an externally imposed host version floor/ceiling belongs there, not repeated here |
