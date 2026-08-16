# Writing `docs/agents.md`

The compact coding-agent file. Write one `##` section per member the manifest
actually selected, in this reading order, grounding each section from the
evidence its member contract requires. `## Conventions` exists only when a
conventions source was found (same condition as the standard
`agents_conventions` document); `## Flows` and `## Terms` exist only when a
flow graph is available.

1. `## At a glance` — folder-index orientation: which retrieval views exist
   and which question each answers.
2. `## Architecture` — `agents-architecture` (durable component paths and the
   constraints that bind them).
3. `## Patterns` — `agents-patterns` (the repeated shapes an agent should
   follow, with the verified command that exercises each).
4. `## Testing` — `agents-testing` (how to run and extend the suite, verified
   commands only).
5. `## Conventions` — `agents-conventions` (evidenced conventions; drop any
   dimension the repository doesn't evidence).
6. `## Tech debt` — `agents-tech-debt` (known rough edges an agent will hit,
   and what not to "fix" incidentally).
7. `## Flows` — `agents-flow` (compact flow lookup grounded in declared flow
   evidence).
8. `## Terms` — `agents-glossary` (term lookup with links to the owning human
   document).

Every path must be durable and every command verified — this file is read by
machines on a token budget, so a stale path costs more here than prose
elsewhere. Link the owning human document for each view instead of restating
it, and link `AGENTS.md` rather than repeating the kernel.

Route to the unfolded siblings. `AGENTS.md`, `CLAUDE.md`, `CLAUDE.local.md`,
and `.claude/settings.json` keep their own fixed paths, and any other selected
document under `docs/agents/` that this file does not merge must appear as a
link in `## Scope and boundaries`.

Ground each section from the repository evidence cited in provenance — one
provenance `sections[]` entry per `##` heading. Do not add sections beyond
what the manifest's `compact_members` for this document actually lists, and do
not route readers into source files. Routing links to sibling documents are
not sections.
