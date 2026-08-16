# `agents_compact`

Content contract for compact document type `agents_compact`.

The merged `docs/agents.md` is the compact form of the coding-agent section.
It holds the section-level orientation (which retrieval views exist and what
each answers) followed by the architecture, patterns, testing, tech-debt,
flow, and term views — plus evidenced conventions when a conventions source
exists — one `##` section per member, in reading order. Each section follows
its member's own content contract; the composed contract for this document
lists the members this project's manifest actually selected.

The fixed host-contract files stay separate at their own paths and are never
folded in here: `AGENTS.md` (the kernel), `CLAUDE.md`, `CLAUDE.local.md`, and
`.claude/settings.json`. Link `AGENTS.md`, never restate it.

| Type | Must present | Keep out | Primary mode | Depth |
|---|---|---|---|---|
| agents_compact | section introduction, at-a-glance view map, scope and boundaries, token-budgeted retrieval views with durable paths, constraints, verified commands, and owning human-doc links; links to every selected document in `docs/agents/` this file does not merge | duplicated human documentation, volatile symbol dumps, facts a member contract keeps out, restated `AGENTS.md` kernel content, direct source-file navigation | Reference | orientation |
