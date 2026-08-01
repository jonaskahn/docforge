# Decision records

A codebase shows what was built. It never shows what was considered and rejected, which constraint forced an awkward choice, or which decision is safe to revisit. That knowledge lives in people's heads until they leave, at which point teams re-litigate settled questions or — worse — quietly undo a decision whose reasoning nobody recorded.

Decision records fix this cheaply. They are the single highest-value addition for both new-engineer onboarding and technical due diligence, because both audiences are asking the same question: *why is it like this?*

## Where and how

`docs/architecture/decisions/NNNN-kebab-slug.md`, numbered from 0001, append-only. The folder README carries the index.

Some teams name the folder `decisions/` rather than `adr/` because the acronym means nothing to a business reader who lands there during a review. That is the naming used here.

## Template

```markdown
# NNNN. <Decision stated as an outcome, not a question>

- **Status:** proposed | accepted | superseded by [NNNN](NNNN-slug.md) | deprecated
- **Date:** YYYY-MM-DD
- **Deciders:** <roles or names>

## Context and problem statement
What forced a decision. The constraints that were real at the time: deadlines,
team size, existing systems, contractual or regulatory requirements. Written so
it makes sense to someone who joins in two years and knows none of the history.

## Considered options
- Option A
- Option B
- Option C

## Decision
We chose <option>, because <the reasoning that was actually decisive>.

## Consequences
**Positive:** what this buys.
**Negative:** what it costs. Name the real trade-off — a record with no negative
consequences is a marketing document and readers discount the whole file.
**Neutral:** what changes without being better or worse.

## Revisit if
The conditions under which this should be reconsidered: a scale threshold, a
dependency's end of life, a team-size change. This turns a historical artifact
into an operational trigger.
```

The "Revisit if" section is not in the classic templates and is worth adding. Without it, decisions calcify: nobody knows whether a five-year-old choice is still load-bearing or merely undisturbed.

This template carries Nygard's five canonical parts (title, status, context, decision, consequences) in the fuller MADR shape (problem statement, considered options, named trade-offs). Two MADR fields are worth adding in larger orgs where a decision touches many teams: **Consulted** (who gave two-way input) and **Informed** (who was told one-way), split out from Deciders; and, where a decision needs enforcement, a **Confirmation** line stating how compliance is verified (a lint rule, an architecture test, a review gate). Add them when they carry weight; omit them when Deciders already says everything.

**An ADR is not a design doc.** An ADR records one decision *already made*, compactly and immutably — it is a durable maintenance artifact. A design doc or RFC is a forward-looking, pre-implementation proposal spanning a whole feature, written to drive discussion before building. This skill documents the system as shipped (see the "document what runs, not aspiration" anti-pattern), so it produces ADRs — the record of what was chosen — not design docs. A live design proposal, if one exists, is the *source* you backfill an ADR from once the decision lands, not a document the tree carries.

## What deserves a record

Write one when a choice is **expensive to reverse**, **not obvious from the code**, or **likely to be questioned later**. Typical: choosing a database, a framework, or a messaging system; defining a tenancy or authentication model; picking a deployment topology; adopting a significant dependency; deliberately *not* doing something (not using an ORM, not sharding yet); accepting known technical debt with a stated repayment condition.

Do not write one for choices a linter enforces, choices that took under an hour, or choices that are self-evident from reading one file. The value of the folder falls as its noise rises.

## Backfilling

Most repos start with years of undocumented decisions. Backfill five to ten load-bearing ones per repo — enough to cover the architecture a reviewer will ask about — rather than attempting completeness.

To find them:

- `git log --diff-filter=A -- <path>` on major directories: when did each subsystem appear?
- Large merge commits and dependency-manifest changes; each significant dependency added is a decision.
- Places where the code does something surprising or awkward. That awkwardness almost always encodes a constraint worth recording.
- Ask the longest-tenured engineer which decisions get re-argued most often. Those are the highest-value records.

Backfilled records must be honest about their provenance. Add a line under the status: `Reconstructed YYYY-MM-DD from commit history and discussion with <person>; the original reasoning may be incomplete.` A reviewer who catches an unmarked retrofit discounts every record in the folder.

## Status discipline

Records are immutable once accepted. When a decision changes, write a new record and update the old one's status to `superseded by [NNNN]` — do not edit history. The chain of superseded records is itself evidence: it shows a team that revisits decisions deliberately rather than drifting.

The folder `README.md` holds the index:

| # | Decision | Status | Date |
|---|---|---|---|
| 0001 | Use PostgreSQL as the primary store | accepted | 2024-03-11 |
| 0002 | Single-tenant schema per customer | superseded by 0009 | 2024-05-02 |

Keep the index sorted by number, not by status; readers arrive with a number from a cross-reference more often than they browse.
