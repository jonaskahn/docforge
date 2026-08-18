# Root writing craft

Writing-craft instructions for `root` group documents. Routes:

- `changelog` → [Changelog](#changelog-writing-craft)
- `root_readme` → [Root README](#root-readme-writing-craft)

## Changelog writing craft

Build entries from released tags and history, then translate only material
changes into what a user, integrator, or operator observes. Keep a version and
release date on every released entry. Put compatibility changes, migrations,
security fixes, and required actions where readers can find them before general
enhancements; link to the owning guide when a change needs procedure depth.

Do not infer a release from a commit, treat merged work as shipped, or add
aspirational items to `Unreleased`. Exclude refactors, test changes, and
dependency churn unless they change behavior, compatibility, security, or a
supported operational contract.

## Illustration

- **Form:** prose — no illustration; keep release categories scannable.
- **Renders:** the categorized entries themselves — version, release date,
  material user-visible change.
- **Trigger:** never — a chronological lookup document; no illustration.

## Connections

| This document owns | Links to | Because |
|---|---|---|
| Released versions, dates, user-visible changes, compatibility notes | `release-notes` | the product-facing view of released impact is owned there |
| A change needing procedure depth | the owning guide (`migration`, `api-versioning`) | linked, never embedded |

## Voice

- **Voice:** plain and outcome-first; a non-specialist finishes the first paragraph.

## Root README writing craft

Make the first screen answer a prospective reader's decision: what this
repository delivers, whether it fits their use, and the shortest verified path
to a useful result. Put one runnable quick start first; link to setup when
environment choices, prerequisites, or recovery would make it longer. Describe
capabilities as outcomes, name meaningful boundaries, and route each reader to
the document that owns their next question.

Do not turn the README into a second setup guide or an architecture overview.
Every status, owner, support channel, command, and link must be evidenced;
omit unknown operational metadata rather than presenting a placeholder as fact.

## Illustration

- **Form:** prose and a routing table — not an architecture diagram.
- **Renders:** the routing table itself — each reader type to the document
  owning their next question.
- **Trigger:** never an architecture diagram — the routing table is the only
  visual, per
  [`../../references/illustration.md`](../../references/illustration.md).

## Connections

| This document owns | Links to | Because |
|---|---|---|
| Purpose, audience, verified quick start, routing | `quickstart` | the under-a-minute verified first result is owned there |
| Environment choices, prerequisites, recovery | `setup-guide` | linked when the quick start would need them |
| The full reader-question routing | `docs-index` | the documentation index owns the complete routing table |

## Voice

- **Voice:** plain and outcome-first; a non-specialist finishes the first paragraph.
