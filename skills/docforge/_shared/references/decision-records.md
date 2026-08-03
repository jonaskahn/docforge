# Decision records

This file owns why a decision deserves a durable record, where it lives, and
its template. Decision records capture what was considered and rejected, the
constraint that forced a choice, and whether it is safe to revisit — the
highest-value addition for onboarding and diligence, since both ask *why is
it like this?*

## Where and how

`docs/architecture/decisions/NNNN-kebab-slug.md`, numbered from 0001,
append-only, named `decisions/` (not `adr/`, which means nothing to a
business reader). The folder README carries the index.

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

Include "Revisit if": without it, nobody can tell whether an old choice is
still load-bearing or merely undisturbed. In larger orgs, add **Consulted**
(two-way input) and **Informed** (told one-way) split out from Deciders, and a
**Confirmation** line naming the lint rule, architecture test, or review gate
that verifies compliance — only when they carry weight beyond Deciders alone.

An ADR records one decision already made, compactly and immutably; it is not
a forward-looking design doc or RFC. Produce ADRs — the shipped decision, not
the proposal — and backfill one from a design doc once the decision lands,
rather than carrying the proposal itself in the tree.

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
