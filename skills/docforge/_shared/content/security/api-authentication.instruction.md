# Api-authentication writing craft

**Preferred illustration:** Follow
[`../../references/illustration.md`](../../references/illustration.md); a
sequence diagram only when a flow (OAuth2 authorization code, mTLS
handshake) has more than two actors — otherwise prose and a credential
table.

Name the scheme by its real category first — API key, bearer token, OAuth2
grant type, mTLS, signed request — because the category determines the
entire integration shape; "authentication" alone tells a caller nothing.
For each scheme in use, state the credential's lifecycle in order: how it
is issued, where it is transmitted, how it is rotated, and what happens
when it expires or is revoked — a scheme description that stops at "send
this header" leaves the caller unable to handle expiry.

Give a failure-mode table, not scattered prose: missing credential, expired
credential, revoked credential, wrong scope — each with its status code and
what the caller should do next. State scope or permission boundaries as
data (a table of scope → capability), not as a paragraph the caller must
parse to find the one scope they need. Never include a real credential,
secret, or token value, including as an "example" — use an obviously
synthetic placeholder.
