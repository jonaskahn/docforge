# Folder-index writing craft

Covers `folder-index`, `docs-index`, `ba-index`, `po-index`, `portfolio-index`,
and `portfolio-decisions-index` — one shared content contract reused by every
group's top-level or subfolder router. A router orients and links; it never
carries a fact a child document owns.

List only the children that exist and are selected for this run, each with a
one-line purpose stated as the reader question that child answers — not its
title restated, not a summary of its contents. Order children the way a
reader would want to navigate them (most-orienting first), not alphabetically.
Never link a document that wasn't selected or hasn't been written yet; an
index promising a future document is worse than no link at all, because it
breaks trust in every other link on the page. When the manifest changes which
children are selected, regenerate the index in the same pass — a stale index
is a defect, not a lag.

An entry is valid only when its child is selected, materialized, and its
relative link resolves from this index. A nested index links exactly one parent
index; use a child link only when that child is part of this run. Do not turn a
missing child into a disabled link, a future-work note, or a prose substitute.

Keep the index itself short enough to scan in one pass. If a group's child
list grows past what fits on one screen, that is a signal the group itself
needs sub-grouping (a nested index), not a signal to compress purposes into
fragments.

## Illustration

- **Form:** prose links only — a bulleted or short-table list of children and
  their one-line purpose.
- **Renders:** nothing beyond the list; a router document never earns a
  diagram of its own.
- **Trigger:** never — per
  [`../../references/illustration.md`](../../references/illustration.md),
  router documents use prose and links exclusively.

## Connections

| This document owns | Links to | Because |
|---|---|---|
| Selected children and their one-line purpose | every listed child document | the index routes; each child owns its own facts, never restated here |
| — | its parent index, if nested | keeps the router chain traceable from the repository root down |
| Nothing else | — | a router that starts explaining a child's content in its own line has stopped being a router — move that detail into the child |
