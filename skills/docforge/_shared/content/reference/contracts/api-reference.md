# `api-reference`

**Reader question** — "What can I call, with what shape in and out, and where's the authoritative source?"

| Mode | Depth | Shape |
|---|---|---|
| Reference | reference | entry-catalog |

_Aliased with: `authentication`, `rate-limits` (same content contract)._

## Must present

| # | Element | At | Done wrong |
|---|---|---|---|
| 1 | The compatibility source named plainly (`openapi.yaml`, generated client types, a GraphQL schema) | lead | "authoritative" left with no concrete referent |
| 2 | Operations grouped by resource or domain | L1 | grouping by HTTP verb or source file |
| 3 | Per operation, in fixed field order: method/path, purpose, request shape, response shape, one realistic example | L2 | field order drifting between operations |
| 4 | Auth requirement and rate-limit class, as table columns | L2 | a repeated paragraph in place of a column |
| 5 | Deprecated operations marked inline with the deprecating version and replacement | L2 | a deprecated operation with no stated replacement |

## Keep out

| Not here | Lives in |
|---|---|
| A hand-copied generated schema or secret | nowhere — derive from the source, never transcribe by hand |
| The response envelope, restated per endpoint | `api_errors` |
| The deprecation policy itself | `api_versioning` |
| Auth mechanism detail | `api_authentication` |
| Rate-limit values | `api_rate_limits` |

## Owns / links

| Owns | Links to | Because |
|---|---|---|
| The operation surface: method/path, request and response shapes, examples | `api_errors` | the shared response envelope is restated once there and linked per endpoint |
| A deprecated operation and its replacement | `api_versioning` | the deprecation policy is owned there |
| Per-operation auth and rate-limit class | `api_authentication`, `api_rate_limits` | each contract is owned by its own document; this one carries the class as a column |
