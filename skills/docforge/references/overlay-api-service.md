# Overlay — API service

**Applies when:** the repo exposes HTTP, gRPC or GraphQL endpoints consumed by anything outside its own process — other services, a front end, or third parties.

An API's documentation *is* part of its product surface. The consumer's entire experience is mediated by it, and the three things they need are: how to make a first successful call, what every field means, and what to do when it fails. The third is the one most often neglected and the one that generates the most support load.

## Additions to the tree

```
docs/
├── product/
│   ├── quickstart.md           authentication to first successful call
│   └── versioning.md           version scheme and deprecation policy
├── architecture/
│   └── dependencies.md         extended with per-integration contracts
├── reference/
│   ├── api.md                  pointer to the generated reference + how to read it
│   ├── errors.md               the error catalog
│   └── rate-limits.md          quotas, headers, backoff guidance
└── security/
    └── authentication.md       schemes, token lifecycle, scope model
```

## Reference documentation: generate it

Hand-written endpoint reference drifts from the implementation within a sprint and then actively misleads. Generate it from the source of truth — an OpenAPI or gRPC/GraphQL schema derived from the code's own type annotations — publish the rendered output, and validate the spec in CI so a change that breaks it fails the build.

`docs/reference/api.md` should therefore be short: where the generated reference lives, how to regenerate it locally, the conventions a reader needs to interpret it (pagination style, filtering syntax, date formats, identifier formats), and what the reference does *not* cover.

## `product/quickstart.md`

The benchmark worth targeting: an unfamiliar developer reaches a successful authenticated call in under twenty minutes. Obtain a credential, make one call, read one response, handle one error. One language, copy-pasteable, with real (non-placeholder) request shapes and a shown response. Resist adding a second language or a comprehensive tour — breadth here defeats the purpose.

## `reference/errors.md` — the error catalog

Two halves: the envelope and the catalog.

**The envelope** — one stable shape for every error the API returns, documented once:

```markdown
## Error response shape
| Field | Type | Description |
|---|---|---|
| `type` | string | Category: `invalid_request`, `authentication`, `permission`, `rate_limit`, `api_error` |
| `code` | string | Stable machine-readable identifier; safe to branch on |
| `message` | string | Human-readable. May change; never parse it |
| `param` | string? | The field at fault, where applicable |
| `request_id` | string | Include this when contacting support |
| `doc_url` | string | Deep link to this code's catalog entry |
```

Two properties matter more than the exact field names. **`code` must be stable** — consumers branch on it, so renaming one is a breaking change. And the envelope should be **additive-only**: new fields may appear, existing ones never change meaning.

**The catalog** — one entry per code, keyed so that `doc_url` can link directly to it:

```markdown
### `resource_not_found`
**Status:** 404 · **Type:** `invalid_request`
**Message:** "No <resource> found with id {id}."
**Cause:** the identifier does not exist, or belongs to a different tenant.
**Resolution:** verify the identifier and that the authenticated caller has access.
**Retryable:** no.
```

The **retryable** flag deserves emphasis: it is what a client library needs in order to implement correct backoff behaviour, and its absence is why so many integrations retry things they should not.

Close with a status-code summary table so a reader can see the whole failure surface at a glance.

## `product/versioning.md`

State the scheme explicitly — URI path, request header, or dated version — and the compatibility rules that go with it. The essential content is the definition of "breaking": which changes consumers must be notified about, and which may ship silently. A conventional split: adding an optional field, adding an endpoint, or adding an enum value to an output are non-breaking; removing or renaming anything, changing a type, adding a required input field, or altering error semantics are breaking.

For deprecations, document the full lifecycle: how consumers are notified (response headers signalling deprecation and sunset dates, plus a link to the migration guide), the notice period, what happens at sunset, and where the migration guide lives. Give a concrete timeline rather than an intention — "at least six months' notice, then the endpoint returns 410" is a commitment a consumer can plan around.

## `architecture/dependencies.md` — integration contracts

For each system the API calls, the contract needs to state failure behaviour explicitly: timeout, retry policy, circuit-breaker thresholds, and what the caller observes when the dependency is down. Document degradation honestly — "if the search service is unavailable, `/search` returns 503; the rest of the API is unaffected" is the kind of statement that makes an incident response short.

## `security/authentication.md`

Supported schemes and when to use which, how credentials are obtained and rotated, token lifetime and refresh, the scope or permission model with the full list of scopes, tenant isolation guarantees, and what a caller should do on a 401 versus a 403. Include the credential-compromise procedure: how to revoke, and how quickly revocation takes effect.

## `reference/rate-limits.md`

The limits themselves, the window and algorithm, which headers communicate remaining quota and reset time, the status code returned when exceeded, and the expected client behaviour on receiving it. If limits differ by plan, endpoint or credential type, tabulate rather than describe.
