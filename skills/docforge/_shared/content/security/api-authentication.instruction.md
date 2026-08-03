# Api-authentication writing craft

Open with the authoritative schema, export, or generator that defines the public
surface and compatibility boundary. Ground issuance, rotation, revocation,
scopes, statuses, and caller actions in code, config, or schema evidence; link
quota and shared error contracts to their reference owners.

**Preferred illustration:** Follow
[`../../references/illustration.md`](../../references/illustration.md); a
sequence diagram only when a flow (OAuth2 authorization code, mTLS
handshake) has more than two actors — otherwise prose and a credential
table.

Name the scheme by its real category first — API key, bearer token, OAuth2
grant type, mTLS, signed request. For each scheme in use, state the
credential's lifecycle in order: how it is issued, where it is
transmitted, how it is rotated, and what happens when it expires or is
revoked.

Give a failure-mode table, not scattered prose: missing credential, expired
credential, revoked credential, wrong scope — each with its status code and
what the caller should do next. State scope or permission boundaries as
data (a table of scope → capability), not as a paragraph the caller must
parse to find the one scope they need. Never include a real credential,
secret, or token value, including as an "example" — use an obviously
synthetic placeholder.
