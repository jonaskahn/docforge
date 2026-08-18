<!-- CRAFT REFERENCE, NOT A GENERATED ARTIFACT.

The compact-layout counterpart of architecture.standard.example.md: the same
fictional expense service, folded into `docs/architecture.md`. Read the two side
by side — every field of the standard document appears here, each repeated block
collapsed to one line per instance. Nothing was summarized away.

Read it beside ../../compact/templates/architecture.template.md and the "Writing
docs/architecture.md" section of ../../compact/instructions.md; update it in the
same change as either of them.

Where a real document would link a neighbour with a relative path, this file
names the neighbour in bold instead, so it stays self-contained and lintable. -->

# Architecture

_Last reviewed: 2026-08-18_

**In one sentence:** this service owns the conversion of expense receipts into
reviewable, reimbursable ledger entries.

This file covers how the service is shaped: what runs where, what depends on
what, and which boundaries a change must not cross. A reader with no prior
project knowledge should finish it able to say where a new receipt source would
belong and which component would have to change with it.

## At a glance

Three runtime roles: a synchronous HTTP surface users wait on, queue consumers
that do everything slow, and a shared domain layer neither may bypass. Receipts
enter through the surface and are finished by the consumers; the domain layer
owns what a receipt and a report mean, and depends on neither.

## Scope and boundaries

This section owns structure and dependency direction. What happens in order, and
who is waiting on each step, is owned by the flows section; the meaning of a
receipt or a report as domain terms is owned by the concepts section. Constraint,
dependency, and debt detail folds in below rather than living in its own file.

## High-level architecture

The service is one deployable API process, one worker process, an object bucket
for images, and a relational ledger. The API is the only process users reach;
the worker is the only process that calls the OCR provider. Both read and write
the same ledger, and neither calls the other directly — the queue is the only
edge between them, which is what lets the worker be restarted during a deploy
without failing a user request.

Upstream, an identity proxy terminates authentication before the API sees a
request. Downstream, the nightly accounting export reads approved reports and is
the only consumer outside this boundary.

## Component design

_Diligence and higher only — omitted entirely at Spine._

```text docforge-role=structure
ledger/
├── api/          synchronous HTTP surface; owns authorization and the receipt row
├── workers/      queue consumers; extraction and notification
├── domain/       receipt and report state machines, shared by api and workers
└── storage/      bucket and database adapters; no business rules
```

The grouping is by runtime role, not by feature: a change to what a receipt
means touches `domain/` alone, a change to where images live touches `storage/`
alone.

**Whiteboxes:** the expense API is decomposed because it holds the only
synchronous path a user waits on and the only place authorization is enforced;
it depends on `domain/` and `storage/`, and neither depends back.

**Request handler** — **Responsibility:** terminates the HTTP request, validates
its shape, and sequences the calls that satisfy it · **Contract:**
`POST /v1/receipts`, `POST /v1/reports/{id}/approve` · **Talks to:** the access
policy for a decision before any write, and the receipt store adapter for the
write itself · **Invariant:** never writes through two adapters in one request,
so no request leaves a partial write the adapter cannot undo · **Failure
boundary:** converts every domain error into a status code; an adapter exception
becomes a `500` and is never retried here, because the client owns the retry.

**Access policy** — **Responsibility:** decides whether an actor may act on a
report, and owns the organization-membership rule · **Contract:**
`may_submit(actor, report)`, `may_approve(actor, report)` · **Talks to:**
nothing; it is a pure function over the actor and the report · **Invariant:** an
approver is never the report's owner, enforced here and nowhere else · **Failure
boundary:** returns a decision, never raises; an unknown actor is a denial.

**Receipt store adapter** — **Responsibility:** writes the image and the receipt
row in a fixed order; the only component that knows both the bucket and the
database · **Contract:** `put_receipt(image, report_id) -> ReceiptId` ·
**Talks to:** the object bucket, then the ledger database · **Invariant:** the
row is never written before the object, so a row always has an image ·
**Failure boundary:** a database failure leaves the orphaned object and raises,
attempting no compensation.

**Quality and change scenarios:** the extraction queue is sized for a burst of
2,000 receipts within one hour, the volume last quarter's month-end close
produced; a second receipt source was anticipated, because the store adapter
takes an image and a report id rather than a request.

```mermaid
accTitle: Runtime scenario — receipt write failing after the object is stored
accDescr: The handler calls the store adapter, which puts the object and then writes the row; on a database failure the adapter raises and the object is left for lifecycle collection.
sequenceDiagram
  participant Handler as Request handler
  participant Adapter as Receipt store adapter
  participant Bucket as Object bucket
  participant Ledger as Ledger database
  Handler->>Adapter: put_receipt(image, report)
  Adapter->>Bucket: put object under content hash
  Bucket-->>Adapter: object key
  Adapter->>Ledger: write receipt row
  Ledger-->>Adapter: constraint violation
  Adapter-->>Handler: raises; object left orphaned
```

The object is written before the row, so this failure leaves an image nobody
references rather than a row with no image — the cheaper of the two, and the
one the bucket lifecycle rule already collects. The success path is the same
sequence with the row write returning a receipt id.

## Constraints

_Diligence and higher only — omitted entirely at Spine._

| Constraint | Limit | Source | Why it exists | What lifting it would take |
|---|---|---|---|---|
| Upload size | 10 MB per image | edge proxy configuration | keeps a single request inside the proxy's buffer | streaming uploads through the API rather than buffering |
| OCR throughput | 500 pages/minute | provider contract | the plan the service is billed on | a contract change, then re-sizing the worker pool |

The service assumes authentication is terminated upstream and that the bucket
and the ledger are in the same region. It deliberately does not do
reimbursement payment — the accounting system owns that, and the nightly export
is the seam.

## Dependencies

_Diligence and higher only — omitted entirely at Spine._

| Package | Purpose | Criticality | If it disappeared |
|---|---|---|---|
| object-store SDK | image storage | high | replaceable behind the store adapter; days |
| database driver | ledger access | high | no substitute in use; weeks |
| HTTP framework | request handling | medium | mechanical rewrite of `api/handlers/` |

The OCR provider is the one hard external service: extraction stops without it,
and the failure is contained by the dead-letter queue rather than by a fallback.
Development dependencies are the usual test and lint toolchain, pinned in the
lockfile and not enumerated here.

## Technical debt

_Diligence and higher only — omitted entirely at Spine._

| Item | Shortcut taken | Cost it imposes | Remediation |
|---|---|---|---|
| Orphaned objects | no compensation when the row write fails | bucket growth, and a manual audit before each storage review | a compensating delete in the adapter, or a transactional outbox |
| Sweep threshold | reconciliation interval is a constant, not configuration | tuning requires a deploy | move it to the same configuration path the worker pool uses |

Both are deliberate and cheap to reverse. The upload-size and throughput bounds
above are not debt — they are imposed from outside and belong in Constraints.
