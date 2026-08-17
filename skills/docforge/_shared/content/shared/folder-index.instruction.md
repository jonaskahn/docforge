# Folder-index writing craft

Covers `folder-index`, `docs-index`, `ba-index`, `po-index`, `portfolio-index`,
and `portfolio-decisions-index` — one shared content contract reused by every
group's top-level or subfolder router. A section README is the reader's
**top-down entry point**: it introduces the section itself, explains how its
topics fit together, and routes to the child documents that own the detail. It
never carries a fact a child document owns.

## Top-down shape

Write the README so a reader who knows nothing about this area can:

1. learn what the section is, why it exists, and who should read it (intro);
2. form a section-level mental model (at a glance);
3. learn what belongs here and which adjacent section owns the rest (scope);
4. pick a reading path for their task (start here);
5. reach every detailed child document, each with the reader question it
   answers (detailed documentation);
6. find related sections (related sections).

List only the children that exist, are selected for this run, are
materialized, and are not agent-context, each with a one-line purpose stated as
the reader question that child answers — not its title restated, not a summary
of its contents. Agent-context outputs are permanently isolated and must never
be linked or mentioned by a generated non-agent document. Order
children the way a reader would want to navigate them (most-orienting first),
not alphabetically. Never link a document that wasn't selected or hasn't been
written yet; an index promising a future document is worse than no link at all,
because it breaks trust in every other link on the page. When the manifest
changes which children are selected, regenerate the index in the same pass.

A section README may mention a project-level fact to give context, but only
when it links immediately to the child document that owns that fact. It never
restates commands, flow steps, rules, configuration, ADR rationale, or failure
analysis, and it never navigates readers into source files — the detailed
documents own implementation depth.

An entry is valid only when its child is selected, materialized, and its
relative link resolves from this index. A nested index links exactly one parent
index; use a child link only when that child is part of this run. Do not turn a
missing child into a disabled link, a future-work note, or a prose substitute.

**In compact layout, a folded child has no file of its own.** Its subject is a
`##` section inside the merged file at the group's `compact_target`, so link
`<merged file>#<section anchor>` — never the standard path, which compact never
materialized. From `docs/README.md` that means `product.md#overview`, not
`product/overview.md`; the manifest entry's `compact_members` lists exactly
which children were folded and into what. Linking the unmaterialized path is a
broken link and fails `scaffold_docs --audit`.

A folded child may be a dynamic instance rather than a catalog document — a
flow, decision, concept, or runbook. Its `compact_members` entry carries the
slug and title that name its section, so the anchor is
`flows.md#<slug>`. Children that did not fold — a group's overflow past
`COMPACT_SECTION_CAP`, and the fixed tooling paths — keep their own paths and
are linked normally.

Keep the section overview itself scannable in one pass. If a group's child list
grows past what fits on one screen, that is a signal the group itself needs
sub-grouping (a nested index), not a signal to compress purposes into
fragments.

## Empty state

When no detailed child is evidenced (for example a decisions or runbooks index
before any record exists), say so honestly and explain when content will
appear. Never emit a placeholder row that names a document that does not exist.

## Illustration

- **Form:** prose, reading-path table, and child map — a bulleted or short-table
  list of children and their one-line purpose.
- **Renders:** at most one small evidence-backed overview diagram when
  relationships are otherwise hard to hold in prose; a router never earns a
  diagram of its own.
- **Trigger:** only when section-level relationships genuinely need it — per
  [`../../references/illustration.md`](../../references/illustration.md),
  router documents use prose and links exclusively.

## Connections

| This document owns | Links to | Because |
|---|---|---|
| Section introduction, at-a-glance, scope, reading paths, and child map | every listed child document | the index routes; each child owns its own facts, never restated here |
| — | its parent index, if nested | keeps the router chain traceable from the repository root down |
| Nothing else | — | a router that starts explaining a child's content in its own line has stopped being a router — move that detail into the child |
