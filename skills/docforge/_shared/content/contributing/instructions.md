# Contributing writing craft

Writing-craft instructions for `contributing` group documents. Routes:

- `contributing_root` → [Contributing-router](#contributing-router-writing-craft)
- `ownership` → [Ownership](#ownership-writing-craft)

## Voice and linking craft

Voice for this group is owned by [`voice.md`](../../references/voice.md):
welcoming imperative, assume competence not context. Name what a linked
document owns before the link ("workspace preparation is owned there,"
never "see `setup_guide`"). What each side of a link owns, and why it is
linked rather than restated, is each contract's `## Owns / links` table,
not this section.

## Contributing-router writing craft

Open with the smallest verified contribution journey: prepare the workspace,
make a focused change, run required checks, and submit through the repository's
actual review path. Distinguish required gates from helpful local checks and
call out the point at which a contributor needs an owner or maintainer decision.
Link each step to its owner: setup, test, convention, security, and ownership
documents hold the detailed rules.

Do not copy commands or policies from those guides, invent a branch, commit, or
review convention, or imply that access is available when it is external.

## Illustration

- **Form:** a short ordered path in prose.
- **Renders:** the journey itself — prepare workspace, make the change, run
  required checks, submit through the actual review path.
- **Trigger:** never — a short ordered path, not a process diagram, per
  [`../../references/illustration.md`](../../references/illustration.md).

## Ownership writing craft

Use current CODEOWNERS or team declarations as primary evidence; use history only
for rationale or chronology when metadata is absent, never as proof that frequent
authorship is ownership. For every row, retain an evidence link or state the area
is unowned or undetermined with its escalation route.

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

## Illustration

- **Form:** a Markdown table.
- **Renders:** one row per owned area — area, responsibility boundary,
  escalation token — the table is the whole document.
- **Trigger:** never — the table is the whole document, per
  [`../../references/illustration.md`](../../references/illustration.md).
