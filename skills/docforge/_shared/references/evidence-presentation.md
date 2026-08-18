# Evidence presentation

Provenance establishes that a claim is grounded. Reader-facing content explains
the claim and routes the reader to the owning documentation. These are
separate concerns.

## Policy

- Every substantive heading has a complete provenance entry in the document's
  folder sidecar, including source paths, roles, and blob hashes.
- Never show a bare source path, line range, or blob hash as a claim citation.
  Provenance carries the evidence; prose carries the claim.
- Send the reader into source only through a **pinned permalink** built from
  the repository base declared in the manifest, and only when they must open,
  edit, run, or inspect that file. A link is not evidence and must never be
  appended to a behavioral claim as if it were.
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

**Name the thing, then link it.** A source, module, or API mention is a
**readable noun phrase** first — always. What changes is what that phrase may
carry: when the reader genuinely needs to open the file, the phrase becomes the
link text of a pinned permalink. Never the reverse: a path is never the visible
text, because the URL already carries the location and the reader needs the
name.

Public API surface is named in its own vocabulary (HTTP method + route, CLI
command, exported name), not as a source location.

| Situation | Write | Never |
|---|---|---|
| Behavioral claim | The checkout handler rejects a cart whose total drifted since pricing. | …rejects it (`src/api/checkout.ts:88`). |
| Claim the reader will want to verify | …rejects it, in [the checkout route](…/blob/…/src/api/checkout.ts#L88-L104). | …rejects it (see `src/api/checkout.ts` lines 88-104). |
| Reader must edit the file | Add the key to [the worker config](…/blob/…/config/worker.yaml). | `[config/worker.yaml](config/worker.yaml)` |
| Module orientation | Request validation lives in the validation module (`src/http/validation/`). | `src/http/validation/schema.ts:12-40` |
| API surface | `POST /v1/checkout` returns `409` when the cart total drifted. | `checkoutHandler(req, res)` at `routes.ts:88` |
| A symbol the reader will grep | the `retryBudget` setting | the private `RetryBudget` class at `internal/retry.ts:14` |
| Flow step | **2.** The pricing service revalidates the cart total, in [the pricing revalidation path](…/blob/…/pricing/cart.js#L88-L96). | **2.** `revalidate()` at `pricing/cart.js:88` |

### How a link gets written

The writer never types a commit sha. It writes the **authoring form** — a
readable label and a repository-relative path with an optional line range:

```markdown
The scheduler claims pending items and marks them `Crawling`
([the crawl-job runner](src/lib/crawler/crawlerjob.js#L397-L399)).
```

`link_sources` then expands it into an absolute permalink pinned to the commit
the document was grounded against, after checking that the path exists and the
range is inside the file. A reference that fails either check is reported and
left untouched, so a broken link fails at write time instead of for a reader.

Three rules keep the result honest:

- **A bare `path:line` in prose is still a defect.** That form is what
  permalinks replace, not a shorthand for them.
- **Omit the line range unless it is the point.** A module-orientation mention
  wants the file; a range that a routine refactor invalidates is worse than
  none.
- **Directory paths** keep a trailing `/` and stay unlinked backticked prose:
  the boundary is the point, not a file.

Agent-context outputs are **unchanged and must stay unchanged**: bare durable
paths, no links, no URLs, no line numbers
([`profiles/audience-coding-agents.md`](profiles/audience-coding-agents.md)).
Audiences whose routed `source_evidence` is `provenance-only` — security
reviewers among them — receive no source links at all.
