# Root writing craft

Writing-craft instructions for `root` group documents. Routes:

- `changelog` → [Changelog](#changelog-writing-craft)
- `root_readme` → [Root README](#root-readme-writing-craft)

## Changelog writing craft

**Preferred illustration:** This is a chronological lookup document; use no
illustration. Keep release categories scannable.

Build entries from released tags and history, then translate only material
changes into what a user, integrator, or operator observes. Keep a version and
release date on every released entry. Put compatibility changes, migrations,
security fixes, and required actions where readers can find them before general
enhancements; link to the owning guide when a change needs procedure depth.

Do not infer a release from a commit, treat merged work as shipped, or add
aspirational items to `Unreleased`. Exclude refactors, test changes, and
dependency churn unless they change behavior, compatibility, security, or a
supported operational contract.

## Root README writing craft

**Preferred illustration:** Follow
[`../../references/illustration.md`](../../references/illustration.md); use prose
and a routing table, not an architecture diagram.

Make the first screen answer a prospective reader's decision: what this
repository delivers, whether it fits their use, and the shortest verified path
to a useful result. Put one runnable quick start first; link to setup when
environment choices, prerequisites, or recovery would make it longer. Describe
capabilities as outcomes, name meaningful boundaries, and route each reader to
the document that owns their next question.

Do not turn the README into a second setup guide or an architecture overview.
Every status, owner, support channel, command, and link must be evidenced;
omit unknown operational metadata rather than presenting a placeholder as fact.
