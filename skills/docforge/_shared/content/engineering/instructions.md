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

**Preferred illustration:** Follow
[`../../references/illustration.md`](../../references/illustration.md); prose per
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
without reads as a suggestion.

## Data-quality writing craft

For each governed dataset, identify producer, transformation boundary, linked
data contract, schema owner, and recovery or runbook handoff. Ground checks in
their implementation; use a bounded ER diagram only for evidenced durable
relationships, never inferred lineage or cardinality.

**Preferred illustration:** Follow
[`../../references/illustration.md`](../../references/illustration.md); a table
mapping dimension to check and enforcement point.

Organize by quality dimension — accuracy, completeness, timeliness,
validity, uniqueness, consistency — and for each, state what is actually
checked and where the check runs (ingestion, transformation, or a
scheduled audit). Distinguish a check that blocks bad data from one
that only observes and alerts on it.

State what happens when a check fails: reject, quarantine, alert-only, or
auto-correct. Where a quality guarantee is evidenced only by a sample or a
subset, say so plainly rather than letting a scoped guarantee read as
universal.

## Publishing writing craft

Before publishing, name artifact identity, version-tag consistency, required
build/test/approval gates, and the non-secret credential mechanism from
manifests, CI, and history. State the evidenced bad-release branch
(unpublish/yank, deprecate, or patch) and link the catalog-selected changelog.

**Preferred illustration:** Follow
[`../../references/illustration.md`](../../references/illustration.md); this is a
how-to — ordered commands and verification, not prose explanation.

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

## Release-guide writing craft

For every release gate and rollback decision, state the evidenced check or
approval, responsible role, release-health signal, and escalation trigger. Link
to the catalog-selected changelog path: it owns released-change history, while
this guide owns the procedure.

**Preferred illustration:** Follow
[`../../references/illustration.md`](../../references/illustration.md); this is a
how-to (Diataxis) — ordered commands and verification, not prose
explanation.

One verified path: prerequisites, version bump (state the scheme —
SemVer or equivalent — and what triggers major versus minor versus patch),
build, verification, publication, rollback — in that order. Follow each
command with its observable success signal, the same discipline
`setup-guide` uses.

Give rollback equal weight to publication, not an afterthought paragraph
at the end. Keep changelog content out — this document is the procedure to
release; `changelog` is the record of what was released.

## Setup-guide writing craft

Ground every prerequisite, version, command, and success signal in manifests,
CI, or local verification. Record unavailable external access as a typed unknown
with its grantor; link configuration semantics and technology inventory to their
reference owners rather than recreating them here.

**Preferred illustration:** Follow
[`../../references/illustration.md`](../../references/illustration.md); use prose and
commands by default, with an ASCII timeline only when sequencing is otherwise
ambiguous.

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

## Styling writing craft

State styling-specific component responsibilities and token-composition
boundaries, linking general hierarchy to `ui-components`. Include
an evidence-backed browser or feature fallback and link the authoritative
support policy, accessibility, and performance claims to their owners.

**Preferred illustration:** Follow
[`../../references/illustration.md`](../../references/illustration.md); a table
for the token system, prose for the theming mechanism.

State the token system (spacing, color, typography scale) as data — name
and value — not prose description. State how theming actually works
(CSS variables, a theme provider, build-time generation) and the
degradation behavior when a token is missing. Keep this distinct from
`ui-components`: that document owns composition, this
one owns the token/theme system components consume.

## Testing-guide writing craft

For each test layer, identify fixture source, setup/reset/cleanup, synthetic or
sensitive-data status, and owner of each shared dependency. Derive commands and
CI-only differences from manifests and CI, give each an observable pass
condition, and retain unsupported environments as explicit limitations.

**Preferred illustration:** Follow
[`../../references/illustration.md`](../../references/illustration.md); prose and
commands per layer, table only for the layer-comparison overview.

Organize by test layer — unit, integration, end-to-end — a rough test
pyramid: fast and narrow at the top of the document, slow and broad at the
bottom. Give each layer its own run command, what it covers, what it
deliberately does not cover, and its isolation model (does it hit a real
database, a container, a mock).

Close with failure diagnosis: what a flaky-looking failure in each layer
usually means, and the first thing to check — the how-to discipline
(Diataxis) applied to "my tests are red," not generic testing philosophy.
