# `agents_compact` — standalone

Standalone content contract for compact document type `agents_compact`.

The merged `docs/agents.md` is the compact form of the coding-agent section,
and in standalone mode it is the only documentation this repository has beyond
the fixed host-contract files. Each `##` section owns its facts rather than
routing to a human-facing owner, following its member's standalone contract.

The fixed host-contract files stay separate at their own paths and are never
folded in here: `AGENTS.md` (the kernel), `CLAUDE.md`, `CLAUDE.local.md`, and
`.claude/settings.json`. Link `AGENTS.md`, never restate it.

Budget each section to roughly 25 lines. Eight members at standalone depth is
where one merged file stops being readable, and a section that cannot answer
its reader question inside that budget is evidence the repository wants the
standard layout instead.

| Type | Must present | Keep out | Primary mode | Depth |
|---|---|---|---|---|
| agents_compact | section introduction, at-a-glance view map with what each section answers, scope and boundaries stating what these views deliberately do not cover, token-budgeted retrieval sections that own their facts with durable paths, constraints, and verified commands; links to every selected document in `docs/agents/` this file does not merge | design rationale, business context, operational procedure, volatile symbol dumps, restated `AGENTS.md` kernel content, direct source-file navigation, links to human-facing documents this run did not generate | Reference | orientation |
