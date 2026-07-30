# Platform-integration writing craft

One section per OS service or platform adapter integrated: what it's used
for, the permission boundary it requires (link
[permissions.md](permissions.md) rather than repeating), the callback
contract, and failure/fallback behavior when the service is unavailable.
Avoid a generic platform-API tutorial — describe this repository's actual
usage, not the platform's documentation.

## Illustration

- **Form:** prose per integration; a table for the permission/callback
  surface.
- **Renders:** one row per OS service/adapter — permission required,
  callback contract, fallback behavior.
- **Trigger:** the table once more than two integrations need comparing —
  per
  [`illustration.md`](../../../references/illustration.md)'s deep-dive budget.

## Connections

| This document owns | Links to | Because |
|---|---|---|
| OS services, adapters, permissions boundary, callbacks, failure and fallback | `security/platform-permissions` | permission rationale and scope is owned there; this document only names which permission each integration requires |
| A host-product (not OS) integration surface | `host-integration` | keeps host-product extension points distinct from OS/runtime adapters |
| A lifecycle transition affected by a platform callback | `application-lifecycle` | avoids re-deriving app lifecycle states here |
