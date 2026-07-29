# Conventions writing craft

**Preferred illustration:** Follow
[`../references/illustration.md`](../references/illustration.md); prose per
convention with one code fence each, table only if comparing many
conventions side by side.

State each convention as evidence, not advice: cite the lint rule, the CI
check, or the repeated pattern across the codebase that actually enforces
or demonstrates it — "we use dependency injection" needs the constructor
pattern shown, not asserted. Drop any convention the repository doesn't
actually evidence; generic style advice ("write clean code") has no place
here regardless of how true it is.

Group by dimension — code structure, error handling, testing, review — and
within each, order by how often a contributor collides with it, not by
when it was adopted. State the consequence of not following the
convention (a failing lint rule, a rejected review) where one exists; a
convention with a real enforcement consequence reads as a rule, one
without reads as a suggestion — be accurate about which this is.
