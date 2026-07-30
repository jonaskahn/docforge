# Decision-record writing craft

**Preferred illustration:** Follow
[`../../references/illustration.md`](../../references/illustration.md); ADRs normally
use prose, with a table for parallel alternatives and consequences.

Each record follows Nygard's ADR shape — title, status, context, decision, consequences —
which the scaffold already carries; the craft is in how the title and consequences read.
State the title as the decided outcome, not the topic ("Use Postgres for session storage,"
not "Database choice"). Write context in past-tense constraints — what was true and forced
the decision — then the decision itself in present-tense commitments. Make alternatives
parallel, one line each, so the tradeoff among them is visible without re-reading. Separate
positive, negative, and follow-up consequences; naming the real cost, not only the benefit,
is what makes a decision record trustworthy. Preserve superseded records rather than editing
them, and link both directions the moment a decision changes — the new record names what it
supersedes, the old record names what superseded it.

The index has no fixed shape of its own: group entries by topic area (architecture,
process, tooling) rather than one flat chronological list, and within a group order newest
first with status (`accepted` / `superseded by NNNN` / `deprecated`) shown inline, so a
reader never opens a superseded record by mistake.
