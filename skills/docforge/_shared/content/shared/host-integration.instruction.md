# Host-integration / extension-points writing craft

Covers `host_integration` and `extension_points` — the host contract and
its extension surface are one relationship viewed from two sides.

- State the host contract first: what this extends, activation events, and
  the compatibility range with host versions.
- For each contribution/extension point: what it lets an integrator do, its
  permission scope, and the sandbox boundary — what it cannot reach.
- State failure behavior when the host is incompatible or the extension
  crashes; avoid a generic "how extension systems work" tutorial in favor of
  this repository's actual contract.
- `host_integration` owns the lifecycle explanation: activation,
  compatibility, sandbox, and failure boundary. `extension_points` is the
  stable lookup surface: for every point, record identifier, trigger,
  input/output contract, permission, compatibility, and source of truth.
- Confirm declarations in manifests or host configuration and compatibility
  in a test matrix when one exists.
- Unsupported versions and unobserved host behavior remain explicit gaps;
  link permission rationale to security rather than duplicating it.

## Illustration

- **Form:** a Markdown table for contribution points and activation events;
  prose for the sandbox and failure boundary.
- **Renders:** per point — identifier, trigger, input/output contract,
  permission, compatibility, source of truth.
- **Trigger:** never — the table and prose carry both views, per
  [`../../references/illustration.md`](../../references/illustration.md).

## Linking craft

Voice for `host_integration` follows `architecture`'s row in
[`voice.md`](../../references/voice.md); voice for `extension_points`
follows `reference`'s row. Name what a linked document owns before the
link ("the block this host extends is named there," never "see
`arch_high_level`"). What each side of a link owns is each contract's
`## Owns / links` table, not this section.
