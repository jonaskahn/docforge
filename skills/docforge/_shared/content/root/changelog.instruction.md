# Changelog writing craft

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
