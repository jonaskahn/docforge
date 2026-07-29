# Ownership writing craft

**Preferred illustration:** Follow
[`../references/illustration.md`](../references/illustration.md); a table
is the whole document.

One row per owned area: the area (a directory, a service, a domain — not
"everything"), the responsibility boundary (what owning it actually means:
review authority, on-call, or both), and the escalation token (a team name
or channel, never an individual's name that will go stale). An area with
no stated boundary reads as "owns everything here," which is rarely true
and creates false expectations.

Order by how often a contributor needs to find an owner — the areas
outside contributors touch most, first. Never invent an owner the
repository doesn't evidence (a CODEOWNERS file, a team declaration); an
unowned area stated plainly is more useful than a guessed owner.
