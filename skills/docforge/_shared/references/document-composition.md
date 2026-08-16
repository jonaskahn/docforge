# Document composition

This file owns topic ownership, promotion, durability, and no-duplication.
Depth per reader is owned by [`depth-and-audience.md`](depth-and-audience.md);
audience-specific packs by
[Business Analysts](profiles/audience-business-analysts.md),
[Product Owners](profiles/audience-product-owners.md),
[coding agents](profiles/audience-coding-agents.md),
[operators](profiles/audience-operators.md), and
[security reviewers](profiles/audience-security-reviewers.md).

## Three document classes

Every document is one of these. The class follows from a single question: does
more than one audience need this exact fact?

| Class | Serves | Structure | Examples |
|---|---|---|---|
| **Aligned** — write once, many read | 2+ audiences need the same subject | Flat file by default; promote to a topic folder (shared `README.md` + audience deep-dive subfiles) only in the pass that writes real subfile content | flow documents, architecture concepts, `product/overview.md`, `reference/limitations.md` |
| **Audience-specific** — one reader | exactly one audience | A plain document in that audience's folder | PO `success-metrics.md`, `release-notes.md`; BA `requirements-traceability.md`; `engineering/setup.md`; `operations/runbooks/`; `security/threat-model.md` |
| **Shared-fact spine** — single source | everyone, as lookup not narrative | One document, stated once, linked everywhere | `reference/glossary.md`, `architecture/dependencies.md`, `reference/configuration.md` |

**Decision rule (per document and per section):**
- More than one audience needs this exact fact? **No** → audience-specific. **Yes** → continue.
- Is it a lookup fact (term, value, code)? **Yes** → shared-fact spine. **No** → aligned.
- Is it a warning or critical constraint? → the topic `README.md` regardless.

BA and PO stay distinct audience-specific packs: BA owns precise business-rule
logic and requirement traceability; PO owns feature value, sequencing, and
release notes. Averaging them into one "business" folder serves neither. Build
BA depth when the codebase encodes non-trivial business logic; build PO depth
when the repo ships user-facing features with an independent release lifecycle;
skip either (and say so) for pure infrastructure or libraries.

The `coding-agents` audience is orthogonal to these three classes: it answers
which consumption modality must hold a token-budgeted context, not which human
reads. `docs/agents/*` never restates a fact a human-facing document already
owns — it links briefly. The only facts this dimension owns are ones no human
document does yet (topology-derived conventions, patterns exemplars).

## One owner per fact

Choose the document whose reader question naturally owns a fact, write it there
once, and link from every other view. Indexes summarize only enough to route;
section READMEs own orientation (introduction, scope, reading path, and child
map) and never duplicate child-owned facts. Agent and audience views do not
restate architecture, flow steps, configuration, limitations, or glossary
definitions.

| Fact | Owner | Linked from |
|---|---|---|
| Business rule logic | flow's `business-analyst.md`, once promoted | PO subfile links; does not restate |
| Feature exists and what it is for | flow document + PO `feature-catalog.md` | BA traceability links to the feature |
| Domain term definition | `reference/glossary.md` | every document links; none restates |
| Flow steps and decision points | flow document | subfiles link for depth, once promoted |
| Feature mechanism | flow's `engineering.md`, once promoted | flow document carries a one-line gist + link |
| Success metric / KPI target | PO `success-metrics.md` | BA omits; does not cross-link |
| Roadmap timing | `product/roadmap.md` | PO README links; does not duplicate |
| Warning / critical constraint | topic `README.md` | subfile may expand it |
| Agent-specific non-obvious convention | `AGENTS.md` or `docs/agents/patterns.md` | nowhere else |
| What the repository is built with | `reference/tech-stack.md` | architecture and setup link; do not restate |
| What it depends on operationally and what breaks | `architecture/dependencies.md` (`dependencies-inventory`) | tech-stack omits failure framing |

## Atomic promotion

A flow or concept begins as one flat file, scaffolded from
[`topic-readme.md`](../content/shared/topic-readme.template.md). Promote it to
`<topic>/README.md` only in the same operation that writes at least one real
deep-dive sibling, scaffolded from
[`audience-deepdive.md`](../content/shared/audience-deepdive.template.md) (its
comment block shapes the file per audience — business-analyst.md,
engineering.md, or product-owner.md). Move the shared content into the
README, update links, and materialize the deep dive atomically. A folder
containing only README is a defect. Building a deep-dive means writing it
and promoting in the same pass — never adding the link first and the file
later.

## Compact demotion

Compact layout demotes a group in the mirror direction, governed by the same
**One owner per fact** table and the same **Depth brake**: several documents
sharing one catalog `compact_group` become `##` sections of one merged file at
the group's `compact_target`, ordered by `compact_order`. Every member keeps
owning its facts; the merged file presents them as named sections with
per-section provenance, never as a merged narrative. One fact still has one
owner — a compact section is a member document hosted in a shared file, not a
rewrite. Reversing the demotion (compact → standard) is atomic promotion run
backwards: scaffold the component files, migrate each section's prose to its
component, retire the merged file — no content lost in either direction (see
`revision.md`).

A group with dynamic children demotes too, and its index becomes the merged
file's candidate matrix rather than a child map: `docs/flows.md` carries the
complete flow matrix plus a section per folded flow. The matrix is the
coverage statement, so every discovered instance keeps a row whether or not it
earned a section.

A group's membership grows with tier — the same `compact_group` can list a
Spine-only core plus Diligence-only additions, and a project's manifest folds
whichever subset its selected tier actually applies.

### Depth brakes

Three caps bound a merged file. They differ in what they measure and where
they are enforced, because only the first is knowable from the catalog alone:

| Cap | Value | Bounds | Enforced by |
|---|---|---|---|
| `COMPACT_CORE_CAP` | 8 | Tier-driven members a group may *declare* — no selector, no condition | `query_catalog --validate` |
| `COMPACT_SECTION_CAP` | 14 | Sections a project actually *materializes*, profile-driven members included | `manage_manifest` when it folds |
| `COMPACT_DYNAMIC_CAP` | 6 | Sections one dynamic type gets in one file | `manage_manifest add --type <t>` |

Past `COMPACT_CORE_CAP` the group is too broad for one file even in compact
layout — authoring a second group with its own `compact_target` is the fix,
not raising the cap. Past `COMPACT_SECTION_CAP` the group spills: the overflow
keeps its own standard paths, linked from the merged file. Past
`COMPACT_DYNAMIC_CAP` the instance stays a row in the file's candidate matrix,
named and evidenced but not expanded. See
[`docs-tree.md`](docs-tree.md) "Compact layout".

## Durability

Write at the slowest-changing useful layer:

- behavior and boundaries instead of private symbols;
- file/module paths instead of line numbers;
- source mentions rendered as human-readable links to the repository file,
  never bare `path:line` references (see `host-neutrality.md`);
- observable contracts instead of implementation trivia;
- decision rationale in append-only records;
- volatile values in reference documents.

A behavior-preserving refactor should not falsify prose.

## Depth brake

Add depth when it changes a reader decision, implementation, diagnosis, review,
or risk judgment. Do not create another file merely because a taxonomy slot
could exist. Prefer the fewest documents that each hold a complete subject in a
single primary mode.
