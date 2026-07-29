# Platform-integration writing craft

**Preferred illustration:** Follow
[`../references/illustration.md`](../references/illustration.md); prose per
integration, table for the permission/callback surface.

One section per OS service or platform adapter integrated: what it's used
for, the permission boundary it requires (link
[permissions.md](permissions.md) rather than repeating), the callback
contract, and failure/fallback behavior when the service is unavailable.
Avoid a generic platform-API tutorial — describe this repository's actual
usage, not the platform's documentation.
