# Engineering writing craft

Writing-craft instructions for `engineering` group documents. Routes:

- `conventions` → [Conventions](#conventions-writing-craft)
- `data_quality` → [Data-quality](#data-quality-writing-craft)
- `library_publishing` → [Publishing](#publishing-writing-craft)
- `release_guide` → [Release-guide](#release-guide-writing-craft)
- `setup_guide` → [Setup-guide](#setup-guide-writing-craft)
- `web_styling` → [Styling](#styling-writing-craft)
- `testing_guide` → [Testing-guide](#testing-guide-writing-craft)

## Conventions writing craft

For every review convention, name the evidenced required reviewer or check, its
applicable artifact or path, and the documented exception route. Cite a durable
rule or representative source and distinguish a mandatory gate from a team habit.

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
without reads as a suggestion.

## Illustration

- **Form:** prose per convention with one code fence each; a Markdown table
  only if comparing many conventions side by side.
- **Renders:** each convention's evidence and its enforcement consequence.
- **Trigger:** the comparison table only when many conventions are compared
  side by side — no diagrams, per
  [`../../references/illustration.md`](../../references/illustration.md).

## Connections

| This document owns | Links to | Because |
|---|---|---|
| Evidenced conventions, their artifacts, enforcement consequences | `testing-guide` | how conventions are exercised by the suite is owned there |

## Voice

- **Voice:** imperative and runnable; every step has an observable result.

## Data-quality writing craft

For each governed dataset, identify producer, transformation boundary, linked
data contract, schema owner, and recovery or runbook handoff. Ground checks in
their implementation; use a bounded ER diagram only for evidenced durable
relationships, never inferred lineage or cardinality.

Organize by quality dimension — accuracy, completeness, timeliness,
validity, uniqueness, consistency — and for each, state what is actually
checked and where the check runs (ingestion, transformation, or a
scheduled audit). Distinguish a check that blocks bad data from one
that only observes and alerts on it.

State what happens when a check fails: reject, quarantine, alert-only, or
auto-correct. Where a quality guarantee is evidenced only by a sample or a
subset, say so plainly rather than letting a scoped guarantee read as
universal.

## Illustration

- **Form:** a Markdown table mapping dimension to check and enforcement
  point.
- **Renders:** per dimension — what is actually checked, where the check
  runs, what happens on failure.
- **Trigger:** the table by default; a bounded Mermaid `erDiagram` only for
  evidenced durable relationships, never inferred lineage or cardinality —
  per the body prose above and
  [`../../references/illustration.md`](../../references/illustration.md).

## Connections

| This document owns | Links to | Because |
|---|---|---|
| Quality dimensions, checks, enforcement points, failure actions | `dataset` | each dataset's identity and lineage contract is owned there |
| Movement and transformation guarantees | `data-flow` | per-handoff guarantees are owned there |
| A failed check's recovery handoff | the relevant `runbook` | recovery procedure is owned there, linked not restated |

## Voice

- **Voice:** imperative and runnable; every step has an observable result.

## Publishing writing craft

Before publishing, name artifact identity, version-tag consistency, required
build/test/approval gates, and the non-secret credential mechanism from
manifests, CI, and history. State the evidenced bad-release branch
(unpublish/yank, deprecate, or patch) and link the catalog-selected changelog.

One verified path: artifact, version source (where the version number
actually comes from — a file, a tag, a generator), build and sign,
registry or channel, verify, rollback or deprecate — in that order. Follow
each step with its observable success signal, the same discipline
`setup-guide` uses.

Give deprecation and rollback the same rigor as the happy path. Never
include a secret value (registry token, signing key); name the mechanism,
never the value. Keep changelog content
out — this document is the mechanics of publishing, not the record of what
was published.

## Illustration

- **Form:** ordered command blocks, each followed by its observable success
  signal.
- **Renders:** artifact → version source → build and sign → registry or
  channel → verify → rollback or deprecate.
- **Trigger:** never — ordered commands and verification, not prose
  explanation, per
  [`../../references/illustration.md`](../../references/illustration.md).

## Connections

| This document owns | Links to | Because |
|---|---|---|
| Artifact identity, gates, publish mechanics, rollback/deprecate | `release-guide` | the project's release procedure is owned there |
| What was published | `changelog` | the record is owned there, linked never restated |

## Voice

- **Voice:** imperative and runnable; every step has an observable result.

## Release-guide writing craft

For every release gate and rollback decision, state the evidenced check or
approval, responsible role, release-health signal, and escalation trigger. Link
to the catalog-selected changelog path: it owns released-change history, while
this guide owns the procedure.

One verified path: prerequisites, version bump (state the scheme —
SemVer or equivalent — and what triggers major versus minor versus patch),
build, verification, publication, rollback — in that order. Follow each
command with its observable success signal, the same discipline
`setup-guide` uses.

Give rollback equal weight to publication, not an afterthought paragraph
at the end. Keep changelog content out — this document is the procedure to
release; `changelog` is the record of what was released.

## Illustration

- **Form:** ordered command blocks, each followed by its observable success
  signal.
- **Renders:** prerequisites → version bump → build → verification →
  publication → rollback.
- **Trigger:** never — ordered commands and verification, not prose
  explanation, per
  [`../../references/illustration.md`](../../references/illustration.md).

## Connections

| This document owns | Links to | Because |
|---|---|---|
| The release procedure: gates, versioning, verification, rollback | `changelog` | the record of what was released is owned there |
| The success-signal discipline | `setup-guide` | each command is followed by its observable signal, the same discipline |

## Voice

- **Voice:** imperative and runnable; every step has an observable result.

## Setup-guide writing craft

Ground every prerequisite, version, command, and success signal in manifests,
CI, or local verification. Record unavailable external access as a typed unknown
with its grantor; link configuration semantics and technology inventory to their
reference owners rather than recreating them here.

This is a how-to, not a tutorial (Diataxis distinction): the reader already wants to run
the thing, not learn why it works. Write a single verified path from prerequisites to a
running instance — one path, not a menu of alternatives.

Use second person and the imperative, present tense, one command per step: "Run `X`," not
"You could run `X`" or "Running `X` will...". Follow each command immediately with the
observable success signal — the exact output or state a reader checks before moving on, not
a paragraph of explanation. Introduce configuration immediately before it is needed, not as
a wall of settings up front. Put common recovery steps beside the failure they fix, keyed by
the symptom the reader is looking at, not by cause. Finish with the smallest useful
verification and a short "what next."

## Illustration

- **Form:** prose and command blocks by default; an ASCII `text` fence
  timeline only when sequencing is otherwise ambiguous.
- **Renders:** the single verified path from prerequisites to a running
  instance.
- **Trigger:** the ASCII timeline only when sequencing cannot be read from
  the steps, per
  [`../../references/illustration.md`](../../references/illustration.md).

## Connections

| This document owns | Links to | Because |
|---|---|---|
| The verified path from prerequisites to a running instance | `quickstart` | the under-a-minute first result is owned there |
| Configuration semantics and the technology inventory | `reference/configuration`, `reference/tech-stack` | owned there, linked not recreated |
| Running the test suite after setup | `testing-guide` | owned there |

## Voice

- **Voice:** imperative and runnable; every step has an observable result.

## Styling writing craft

State styling-specific component responsibilities and token-composition
boundaries, linking general hierarchy to `ui-components`. Include
an evidence-backed browser or feature fallback and link the authoritative
support policy, accessibility, and performance claims to their owners.

State the token system (spacing, color, typography scale) as data — name
and value — not prose description. State how theming actually works
(CSS variables, a theme provider, build-time generation) and the
degradation behavior when a token is missing. Keep this distinct from
`ui-components`: that document owns composition, this
one owns the token/theme system components consume.

## Illustration

- **Form:** a Markdown table for the token system; prose for the theming
  mechanism.
- **Renders:** tokens as data — name and value — and how theming actually
  works.
- **Trigger:** never — the token table plus theming prose, per
  [`../../references/illustration.md`](../../references/illustration.md).

## Connections

| This document owns | Links to | Because |
|---|---|---|
| The token/theme system, degradation when a token is missing | `ui-components` | component composition and general hierarchy are owned there |
| Support policy, accessibility, performance claims | `browser-support`, `accessibility`, `performance-budgets` | each claim is linked to its owner, not restated |

## Voice

- **Voice:** imperative and runnable; every step has an observable result.

## Testing-guide writing craft

For each test layer, identify fixture source, setup/reset/cleanup, synthetic or
sensitive-data status, and owner of each shared dependency. Derive commands and
CI-only differences from manifests and CI, give each an observable pass
condition, and retain unsupported environments as explicit limitations.

Organize by test layer — unit, integration, end-to-end — a rough test
pyramid: fast and narrow at the top of the document, slow and broad at the
bottom. Give each layer its own run command, what it covers, what it
deliberately does not cover, and its isolation model (does it hit a real
database, a container, a mock).

Close with failure diagnosis: what a flaky-looking failure in each layer
usually means, and the first thing to check — the how-to discipline
(Diataxis) applied to "my tests are red," not generic testing philosophy.

## Illustration

- **Form:** prose and command blocks per layer; a Markdown table only for
  the layer-comparison overview.
- **Renders:** each layer's run command, coverage, isolation model, and
  failure diagnosis.
- **Trigger:** the overview table only — no diagrams, per
  [`../../references/illustration.md`](../../references/illustration.md).

## Connections

| This document owns | Links to | Because |
|---|---|---|
| Test layers, run commands, isolation models, failure diagnosis | `conventions` | testing conventions and their enforcement are owned there |
| Which checks gate a release | `release-guide` | the release procedure owns its gates |

## Voice

- **Voice:** imperative and runnable; every step has an observable result.
