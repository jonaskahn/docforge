# Evidence presentation

Provenance establishes that a claim is grounded. Reader-facing content explains
the claim and routes the reader to the owning documentation. These are
separate concerns.

## Policy

- Every substantive heading has a complete provenance entry in the document's
  folder sidecar, including source paths, roles, and blob hashes.
- Never show source paths, line ranges, blob hashes, or source-code links as
  claim citations in generated documentation.
- Show a repository path only when the reader must open, edit, run, or inspect
  that file. It is not evidence and must not be appended to a behavioral claim.
- Use a compact `Related` footer only for generated documentation that already
  exists and owns an adjacent topic. Omit the footer when there is no useful
  destination.

```markdown
> **Related:** [Dead-letter replay](../flows/dlq-replay.md), [Worker recovery](../operations/worker-recovery.md).
```

- `compact` permits a short `Related` footer with relevant generated documents.
- `traceability` permits an evidence or traceability table when the table is
  itself the document's subject, such as a threat register or backlog record.
- `none` omits reader-facing routing while retaining provenance.

An evidence gap is explicit prose, not an empty footer: `Repository evidence
does not establish the retention period.`

## Naming things a reader can find

A source, module, or API mention is a **readable noun phrase** first. A
repository path may follow it, in backticks, in parentheses — never as a
Markdown link, never with a line number, and only when the reader must open,
edit, run, or inspect that file. Public API surface is named in its own
vocabulary (HTTP method + route, CLI command, exported name), not as a source
location.

| Situation | Write | Never |
|---|---|---|
| Behavioral claim | The checkout handler rejects a cart whose total drifted since pricing. | …rejects it (`src/api/checkout.ts:88`). |
| Reader must edit the file | Add the key to the worker config (`config/worker.yaml`). | `[worker config (config/worker.yaml)](config/worker.yaml)` |
| Module orientation | Request validation lives in the validation module (`src/http/validation/`). | `src/http/validation/schema.ts:12-40` |
| API surface | `POST /v1/checkout` returns `409` when the cart total drifted. | `checkoutHandler(req, res)` at `routes.ts:88` |
| A symbol the reader will grep | the `retryBudget` setting | the private `RetryBudget` class at `internal/retry.ts:14` |
| Flow step | **2.** The pricing service revalidates the cart total. | **2.** `revalidate()` at `pricing/cart.js:88` |

Directory paths keep a trailing `/` and are preferred over file paths whenever
the boundary, not the file, is the point. Agent-context outputs are
unchanged: bare durable paths, no links, no line numbers
([`profiles/audience-coding-agents.md`](profiles/audience-coding-agents.md)).
