# Audience matrix — classes, ownership, and the BA/PO split

Purpose: decide, for any document or fact, which of three classes it belongs to and which
folder owns it — so a subject read by several audiences is written once, not re-stated in
parallel per-audience folders. Read `document-composition.md` for the mechanics (the
flat-by-default/atomic-promotion pattern, the invariants, the durability rules) and `depth-and-audience.md`
for how deep each reader goes.

## Three classes of document

Every document is one of these. The class follows from a single question: **does more than
one audience need this exact fact?**

| Class | Serves | Structure | Examples |
|---|---|---|---|
| **Aligned** — write once, many read | 2+ audiences need the same subject | Flat file by default (`flows/<flow>.md`); promoted to a topic folder — common `README.md` + audience deep-dive subfiles — only in the pass that writes real subfile content | flow documents, architecture concepts, `product/overview.md`, `reference/limitations.md` |
| **Audience-specific** — one reader | exactly one audience | A plain document in that audience's folder | PO `success-metrics.md`, `release-notes.md`; BA `requirements-traceability.md`; `engineering/setup.md`; `operations/runbooks/`; `security/threat-model.md` |
| **Shared-fact spine** — single source | everyone, as lookup not narrative | One document, stated once, linked everywhere | `reference/glossary.md`, `architecture/dependencies.md`, `reference/configuration.md` |

**Decision rule (per document and per section):**
- More than one audience needs this exact fact? **No** → audience-specific document. **Yes** → continue.
- Is it a lookup fact (term, value, code)? **Yes** → shared-fact spine. **No** → aligned topic folder.
- Is it a warning or critical constraint? → the topic `README.md` regardless, per invariant 2.

This keeps the single-reader documents where they belong, and adds the **aligned** middle
class so a subject three audiences care about is written once — not re-framed in three
folders that then drift apart.

## Why BA and PO stay distinct

Business Analyst and Product Owner both sit "between business and engineering," so they get
merged into one "business" folder. They read different things in a different order:

| Question | BA | PO |
|---|---|---|
| What does the business rule precisely say? | Yes — primary artifact | No — cares that it exists, not its exact logic |
| Why does this requirement exist, traceable to a stakeholder ask? | Yes | Only at epic level |
| Is this feature worth building; has it paid off? | No | Yes — primary question |
| What ships next, and in what order? | No | Yes |
| What can a customer expect right now, in plain language? | No (that is `product/overview.md`) | Yes, as release notes |

So they are separate readers with separate **audience-specific** documents — and, once a flow
is promoted to a folder, separate deep-dive subfiles (`business-analyst.md`, `product-owner.md`).
One folder averaged across both serves neither.

## Fact ownership

When a fact could plausibly live in more than one place, this table decides the single owner.
Everywhere else links to it; nothing is pasted twice.

| Fact | Owner | Linked from |
|---|---|---|
| Business rule logic (thresholds, eligibility, exceptions) | flow's `business-analyst.md`, once promoted | PO subfile links; does not restate |
| Feature exists and what it is for | flow document (L0) + PO `feature-catalog.md` for the catalog view | BA traceability links to the feature |
| Domain term definition | `reference/glossary.md` (spine) | every document links; none restates |
| Flow steps and decision points | flow document (L1, plain) | subfiles link for depth, once promoted |
| Feature mechanism (how it runs) | flow's `engineering.md`, once promoted | flow document carries a one-line gist + link |
| Success metric / KPI target | PO `success-metrics.md` | BA does not need it — omit, don't cross-link |
| Roadmap timing | `product/roadmap.md` (spine) | PO README links; does not duplicate the dated table |
| Warning / critical constraint | topic `README.md` (invariant 2) | subfile may expand it |
| Agent-specific non-obvious convention (topology anomaly) | `AGENTS.md` §5 or `docs/agents/patterns.md` | nowhere else — no human document needs it |

## A fourth dimension: machine consumption (the agent-context overlay)

The three classes above sort content by *which human reads it*. The `agent-context` overlay (`overlay-agent-context.md`) answers a different question: *what must an AI coding agent hold in a token-budgeted context window before it edits this code* — not which human, but which consumption modality.

This is not a peer of the three classes; it's orthogonal to all of them. The governing rule is stricter than R2 alone: **`docs/agents/*` never restates a fact a human-facing document already owns — it links to it, briefly.** `docs/agents/tech-debt.md` doesn't re-derive `architecture/tech-debt.md`; it's a stub with a link. `docs/agents/glossary.md` doesn't redefine a term `reference/glossary.md` already owns; it's a filtered linking view. The only facts this dimension genuinely owns are ones no human document does yet — topology-derived non-obvious conventions, and `docs/agents/patterns.md`'s complexity/exemplar content. Everywhere else, the agent-facing file does *less* work than its human counterpart, not a compressed version of the same work.

## When to build audience depth at all

- Build a `business-analyst.md` deep-dive (or the audience-specific BA documents) when the
  codebase encodes non-trivial business logic — validation rules, approval thresholds,
  eligibility conditions, pricing — that a non-engineer would otherwise read source to find.
- Build PO depth when the repo ships user-facing features with an independent release
  lifecycle someone actively plans against.
- Skip either, and say so explicitly, when the repo is pure infrastructure or a library with
  no embedded business logic and no independent release cadence. An unrequested, empty, or
  dangling (linked-but-missing) audience file is the same anti-pattern as an unfilled scaffold.
- Building a deep-dive means writing it and promoting the flow to a folder in the same pass —
  never adding the link first and the file later. See `document-composition.md`.

Provenance is tracked per document and per section regardless of class — see
`provenance-tracking.md`. Alignment governs prose (write once, link) not provenance.
