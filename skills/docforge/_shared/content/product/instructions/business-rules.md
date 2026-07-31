# Business-rules writing craft

**Preferred illustration:** This is a rule lookup; use a repeatable rule block
or table, not a diagram.

Make every rule independently reviewable. Give it a stable identifier and plain
language statement, then state its trigger, outcome, exceptions, owning process,
source-enforced condition, and executable verification when one exists. Separate
rules that happen to share a code path when their triggers or outcomes differ;
surface precedence when rules conflict or one overrides another.

Do not promote a method, field, or branch name into a rule without proving its
condition and effect. Link to the process and tests rather than duplicating
their ordered steps or test implementation.
