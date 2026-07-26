# Overlay: Product Owner

**Applies when:** the repo ships user-facing features with an independent release cadence that a product owner actively plans against.

Adds three or four files under `docs/product/product-owner/`.

## `README.md`

Index, plus a cross-link to `../business-analyst/` if that overlay also exists.

## `feature-catalog.md`

Distinct from the spine's `capabilities.md`: that file states what the product does, for any reader; this one reframes the same feature set around *value and status*, for planning conversations.

```markdown
### Feature: <name>
**Value:** <the business or user outcome, one sentence>
**Status:** shipped (vX.Y) / in progress / planned / deprecated (sunset date)
**Owns:** <which flow(s) implement it — link to `business-analyst/process-flows.md` if that overlay exists, otherwise to `architecture/high-level.md`>
**Depends on:** <other features or external services this needs>
```

Do not restate `capabilities.md`'s descriptions — link to them. This file's contribution is status and value framing, nothing `capabilities.md` already carries.

## `success-metrics.md`

One entry per feature or epic that has a stated success metric — only where the metric is either instrumented in code (an emitted event, a logged counter) or explicitly given by a stakeholder. Never invent a target number.

```markdown
### <Feature>
**Metric:** <what's measured>
**Instrumented via:** `<symbol/event name>`, or "not instrumented — flag"
**Target:** <only if stated by a stakeholder; omit the row rather than guess>
```

## `release-notes.md`

User-facing changelog, distinct from the root `CHANGELOG.md`, which is commit-level and technical. This one is feature-framed: "Approval threshold is now configurable per account," not "refactor: extract ApprovalConfig." Build it by walking merge commits since the last entry and translating each into user impact; skip purely internal changes (refactors, dependency bumps) — a PO-facing changelog that lists internal noise trains readers to stop reading it.

## `backlog-traceability.md` (optional)

Only build this file if an issue tracker's IDs actually appear in commit messages or code comments — epic/story ID → feature → code flow, so a PO can answer "what did ticket X actually change" without archaeology. Skip it entirely, rather than fabricate a mapping, if no ticket references exist anywhere in history.

## Non-negotiable specific to this overlay

Status and value are the two claims this overlay must never overstate. "Shipped" means the code path is reachable and tested, not merely present in the tree. "Value" is the stated business reason a stakeholder gave, not an assumed one — where that reason isn't recorded anywhere accessible, write "value not documented at time of writing" rather than supply a plausible-sounding justification.
