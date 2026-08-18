# Decision-record writing craft

Which decisions earn a record, and how to recover them from a repository that
never wrote any, are owned by
[`../../references/decision-records.md`](../../references/decision-records.md) —
including the five-to-ten backfill ceiling and the exact git signals. Candidates
reach this document through `harvest_candidates` and the write-start selection
gate, never by invention.

- Each record follows Nygard's ADR shape — title, status, context, decision,
  consequences — which the scaffold already carries; the craft is in how the
  title and consequences read.
- State the title as the decided outcome, not the topic ("Use Postgres for
  session storage," not "Database choice").
- Write context in past-tense constraints — what was true and forced the
  decision — then the decision itself in present-tense commitments.
- Make alternatives parallel, one line each, so the tradeoff among them is
  visible without re-reading.
- Separate positive, negative, and follow-up consequences; naming the real
  cost, not only the benefit, is what makes a decision record trustworthy.
- Preserve superseded records rather than editing them, and link both
  directions the moment a decision changes — the new record names what it
  supersedes, the old record names what superseded it.
- The index has no fixed shape of its own: group entries by topic area
  (architecture, process, tooling) rather than one flat chronological list,
  and within a group order newest first with status (`accepted` /
  `superseded by NNNN` / `deprecated`) shown inline, so a reader never opens
  a superseded record by mistake.
- Ground every record in a direct decision source or label it
  `Reconstructed` with the history or discussion used, its date, and what
  may be incomplete. Do not promote a later commit's implementation into
  contemporaneous rationale.
- The index is routing metadata only: number, outcome title, status, date,
  and link; group by topic and order newest first within that group.
- A portfolio decision links the member ADRs that establish it and must not
  rewrite their local rationale as a new shared fact.

## Illustration

- **Form:** prose, with a table for parallel alternatives and their
  consequences.
- **Renders:** each alternative as a row with its tradeoff, when more than
  one alternative was seriously considered.
- **Trigger:** the table only when two or more alternatives need comparing
  side by side — per
  [`../../references/illustration.md`](../../references/illustration.md).

## Connections

| This document owns | Links to | Because |
|---|---|---|
| Title, status, context, decision, consequences for one decision | the architecture/domain document the decision shaped | the record owns rationale; the shaped document (e.g. `architecture-high-level`) owns the resulting fact, linked not restated |
| A decision this one supersedes | the superseded record, both directions | preserves history — old and new records must reference each other explicitly |
| Cross-repository decision evidence | `portfolio-decision`'s member links, when scope is portfolio-wide | keeps a portfolio decision traceable to the member records it draws on |
