# Documentation tree

This file owns paths, naming, tiers, and placement. The canonical selectable
path list is `.metadata/catalog/` (queried via `runtime/cli/python/query_catalog.py` / `runtime/cli/js/query_catalog.js`; see `runtime/catalog/README.md`).

## Naming and placement

- Reader documentation lives under `docs/`.
- Root files exist only where repository tooling expects them: `README.md`,
  `CHANGELOG.md`, `CONTRIBUTING.md`, `SECURITY.md`, and explicitly selected
  agent kernels/local configuration.
- Portfolio documents live under `docs-portfolio/`.
- Collection folders use plural nouns; single-subject areas use singular nouns.
- Every selected folder index is a manifest document. Its child map is generated
  from selected manifest entries; the section overview around it (introduction,
  scope, reading paths) is authored from repository evidence. A section README
  is finalized after its child documents, so it links only materialized
  documents.
- Actual flows, decisions, runbooks, datasets, concepts, migrations,
  portfolio decisions, and epics are dynamically discovered. Do not create
  example files.
- A flow or concept stays a flat file until real deeper material is written in
  the same operation; see `document-composition.md`.

## Tiers

`spine`, `diligence`, and `portfolio` are the only tier identifiers, in that
order. Higher tiers include lower tiers.

### Spine

Spine supplies the universal front doors and operating baseline:

```text
README.md
CHANGELOG.md
docs/
  README.md
  product/README.md
  product/overview.md
  architecture/README.md
  architecture/high-level.md
  flows/README.md
  engineering/README.md
  engineering/setup.md
  engineering/testing.md
  reference/README.md
  reference/configuration.md
  reference/limitations.md
  reference/tech-stack.md
```

### Compact layout

Layout is a second axis alongside tier, but not every combination exists:

| Layout | Spine | Diligence | Portfolio |
|---|---|---|---|
| `standard` | ✓ | ✓ | ✓ |
| `compact` | ✓ | ✓ | **✗** |

**A Portfolio root is always `standard`.** Portfolio is cross-repository
diligence, and its value is per-member separation — an inventory row and a
system-context view per repository, with decisions and epics as dynamic
indexes that never fold. Collapsing the collection layer into one file erases
exactly the distinctions the tier exists to make. `init` and `reconcile`
reject an explicit `--layout compact` at that tier and force a *detected*
compact layout to `standard`, recording `decided_by: "tier-constraint"`.

Member repositories inside a collection are documented at Spine or Diligence,
each with its own manifest and its own layout. A member may be compact while
the collection root is standard; Docforge never propagates a layout across a
repository boundary.

Scale suggests a layout — it never changes the tier default. A compact tier
covers the **same subjects** as its standard counterpart; it stops giving each
subject its own file. Documents sharing a catalog `compact_group` collapse
into one merged file at the group's `compact_target`, one `##` section per
member in `compact_order`, with the members recorded on the manifest entry so
provenance and revise can trace them back.

**In compact layout the file count is a function of layout and tier alone.**
Confirming a shape adds sections, not files. Discovering ten flows adds
sections, not files. That bound is the point of the layout: a reader can hold
the whole tree in their head, and a user picking compact at intake knows what
they are getting before discovery runs.

#### Compact reference trees

A repository with no confirmed profiles and the default audiences:

```text
Compact Spine (8 files, down from 15)     Compact Diligence (15 files, down from 34)

README.md                                 README.md
CHANGELOG.md                              CHANGELOG.md
docs/                                     CONTRIBUTING.md
  README.md                               SECURITY.md
  product.md                              docs/
  architecture.md                           README.md
  flows.md                                  product.md
  engineering.md                            architecture.md
  reference.md                              concepts.md
                                            flows.md
                                            decisions.md
                                            engineering.md
                                            reference.md
                                            operations.md
                                            security.md
                                            contributing.md
```

Three groups appear only when their audience is confirmed, and each folds to
one file of its own rather than swelling a neighbour: `docs/agents.md`
(coding agents), `docs/business-analyst.md`, `docs/product-owner.md`. Coding
agents additionally bring the tooling-owned paths `AGENTS.md`, `CLAUDE.md`,
`CLAUDE.local.md`, and `.claude/settings.json`, which never fold. Every
agent-context output is self-contained and sits outside generated documentation
navigation: no generated document links or refers to it, and it contains no
documentation reference itself. See the permanent isolation boundary in
[`document-composition.md`](document-composition.md). With three shapes, a platform, three
concerns, and all seven audiences confirmed, Compact Diligence is 22 files
against Standard's 70 — the standard tree grew by 36, the compact one by 7.

#### What folds

| Member kind | Folds | Section it becomes |
|---|---|---|
| Tier-driven core (no selector, no condition) | Always | One `##` per member, in `compact_order` |
| Profile- and audience-driven | Always | One `##` per selected member, after the core |
| Dynamic instances (flows, decisions, concepts, runbooks, datasets, migrations) | Up to the section budget | One `##` per instance, plus a row in the file's candidate matrix |
| Fixed tooling paths (`README.md`, `CHANGELOG.md`, `CONTRIBUTING.md`, `SECURITY.md`, agent host outputs) | Never | — |

**Two caps bound a merged file**, both owned by
[`document-composition.md`](document-composition.md) "Depth brakes":
`COMPACT_CORE_CAP` (8) limits the tier-driven members a group may *declare*
and is enforced by `query_catalog --validate`; `COMPACT_SECTION_CAP` (14)
limits the sections a project actually *materializes* and is enforced by
`manage_manifest` when it folds.

`COMPACT_DYNAMIC_CAP` (6) is the section budget for one dynamic type in one
file. Every discovered instance still appears in the merged file's candidate
matrix — coverage is stated in full — but only the first six are expanded into
sections; the rest stay matrix rows, the same main/deferred split the flow
index already uses. `manage_manifest add --type <t>` refuses past the budget
rather than silently dropping the instance.

**A group that exceeds `COMPACT_SECTION_CAP` spills.** The merged file keeps
its core members plus profile sections in `compact_order` until the cap is
reached; the overflow stays at its own standard path and is linked from the
merged file. Spilling is the pre-fold behavior applied as a safety valve, so a
repository that is simultaneously five shapes degrades to the standard tree
for the excess instead of producing one unreadable file. `manage_manifest
preview` names any group that spilled.

Three routing rules follow, and all are mechanically checked by
`scaffold_docs --audit`:

- A non-agent merged file links every selected, materialized document in the
  folders it stands for that is not one of its own `compact_members`. A merged file can
  stand for a folder its own path does not name — `docs/decisions.md` stands
  for `docs/architecture/decisions/` — and for more than one, so the folders
  come from the members it merged, not from its path.
- An index links a folded member at `<compact_target>#<member-anchor>`, never
  at the standard path that compact never materialized. `docs/README.md`
  linking `reference/configuration.md` in a compact tree is a broken link;
  `reference.md#configuration` is the correct target.
- A generated non-agent index never lists or mentions an agent-context child,
  in either layout. Agent-context outputs also never link their component,
  compact, kernel, peer, or human-facing documents. The seven compact topic
  members remain within the compact core budget, so they require no spill
  navigation.

`project.scale.layout` records which tree was generated; switching layouts is a
selection change like any other and flows through the revise preview and
retirement (see `revision.md`).

### Diligence

Diligence adds detailed architecture, discovered flows and decisions, risk and
dependency records, security, operations/runbook indexes, release/contribution
guidance, and a glossary. Conditional conventions documents appear only when a
conventions source exists.

`docs/flows/README.md` exists at Spine as the rendered complete candidate
matrix backed by `.docforge/flow-index.json`. Revise flow creates stub
`docs/flows/{slug}.md` files for every harvested candidate. Diligence adds
full deep-dive flow documents only for main-priority rows; deferred-priority
stubs remain discoverable in the matrix until promoted.

In compact layout the matrix and the deep dives share one file, `docs/flows.md`
— the matrix is its `## Flow candidate matrix` section and each deep dive is a
`##` section below it, up to `COMPACT_DYNAMIC_CAP`. Compact writes no stub
files: a candidate is either a section or a matrix row.

### Portfolio

Portfolio includes all Diligence documents plus:

```text
docs-portfolio/
  README.md
  repo-inventory.md
  system-context.md
  decisions/README.md
  epics/README.md
  security-posture.md
  operations.md
  diligence-index.md
  glossary.md
```

Actual cross-repository decisions and epics are dynamic entries under
`docs-portfolio/decisions/` and `docs-portfolio/epics/`; both collection
indexes are catalog records (`portfolio_decisions_index`,
`epics_index`). Collection procedure and cross-repository writing
specifics live in [`portfolio.md`](portfolio.md).

## Typed profiles

The catalog owns five independent dimensions:

- **shapes** describe what the repository delivers and select durable document
  packs;
- **platforms** describe where artifacts run and add platform constraints;
- **frameworks** supply detection, terminology, evidence queries, and verified
  commands but do not add a parallel framework tree;
- **concerns** add evidenced cross-cutting documents or sections;
- **audiences** add reader-specific views.

All dimensions are multi-select. Shared paths are defined once with multiple
selectors, retain every matching origin, and never duplicate. Selecting any
child also selects each cataloged ancestor `README.md`; there are no manual
folder-index trigger lists.

### Shape-owned paths

The catalog is authoritative. Detailed composition notes, each carrying its
own exact path additions, are available for 11 repository shapes:
[API-service](profiles/shape-api-service.md), [web-app](profiles/shape-web-app.md),
[library/SDK](profiles/shape-library-sdk.md), [data-pipeline](profiles/shape-data-pipeline.md),
[infrastructure-platform](profiles/shape-infrastructure-platform.md),
[mobile-app](profiles/shape-mobile-app.md), [desktop-app](profiles/shape-desktop-app.md),
[cli-tui](profiles/shape-cli-tui.md), [game](profiles/shape-game.md),
[embedded-iot](profiles/shape-embedded-iot.md), and [smart-contract](profiles/shape-smart-contract.md).

Three catalog layout groups select their document packs directly from the
catalog with no separate profile guide:

```text
worker-serverless
  docs/architecture/triggers-and-jobs.md
  docs/operations/job-reliability.md

plugin-extension
  docs/architecture/host-integration.md
  docs/reference/extension-points.md
  docs/operations/distribution.md

ml-system
  docs/architecture/model-lifecycle.md
  docs/reference/model-card.md
```

Platform-specific packaging, signing, permissions, lifecycle, compatibility,
and distribution details are sections inside their owning documents rather
than one file per framework.

### Audience-profile roots

Audience-profile roots are intentionally visible in the plan, not hidden as
generic conditionals. Only the BA process/rule/traceability set and the agent
flow/flow-derived glossary views require a flow graph; Product Owner
documents use code, manifests, history, and ticket/stakeholder evidence as
applicable and do not globally hard-gate on flow data. Each profile's exact
generated paths are listed in its own composition notes:
[Business Analysts](profiles/audience-business-analysts.md),
[Product Owners](profiles/audience-product-owners.md),
[coding agents](profiles/audience-coding-agents.md),
[operators](profiles/audience-operators.md), and
[security reviewers](profiles/audience-security-reviewers.md).

## Existing documentation

Before moving existing documents, inventory and propose one action per file:
keep, migrate, merge, archive, or delete. Moving, merging, archiving, and
deleting require explicit user approval. Archive approved obsolete material
under `docs/_archive/<year>/` (or `docs-portfolio/_archive/<year>/`); audits
exclude that directory.

## Unmanaged documents

An **unmanaged document** is a `.md` / `.mdx` file under `docs/` or
`docs-portfolio/` that has no manifest entry — Docforge did not generate it
and does not own it (user-written notes, other tools' output, hand-maintained
guides). When a run first sees one, it asks once per file:

- **Keep self-managed** (recommended) — leave the file in place and record it
  in `project.unmanaged_docs` (`[{path, decided_at}]`) with
  `manage_manifest.{py,js} unmanaged add`. Self-managed docs are **never
  tracked, never re-asked**: scans and audits skip them, no scaffold or
  template touches them, and no future run offers to track or overwrite them.
- **Archive** — move the file into `docs/_archive/<year>/` (or
  `docs-portfolio/_archive/<year>/`) with
  `manage_manifest.{py,js} unmanaged archive`. This is a file move and always
  requires explicit user approval (never under `--auto-accept`).

If the user later asks to **update** an unmanaged doc, update its content
with the normal grounding and writing quality — but never add a manifest
entry, never stamp Docforge provenance, and keep it in `unmanaged_docs`: the
file keeps belonging to the user. `unmanaged remove` forgets the record
without touching the file (the doc is then foreign again and will be asked
about on the next run).

**Root `README.md` special case.** Catalog `root_readme` targets the
repo-root `README.md`. When that file already exists and is non-trivial /
valuable (substantial user-facing content, not an empty stub), do not silently
overwrite it with the Docforge template. Present exactly **migrate** / **skip**
/ **rewrite** and wait for confirmation before any write:

- **migrate** — reshape into the `root_readme` contract/template; preserve
  purpose, audience, install/quickstart, and other key facts;
- **skip** — leave the file untouched; mark `root_readme` skipped for this run;
- **rewrite** — replace with the Docforge `root_readme` template from fresh
  evidence.

`--auto-accept` does not waive this choice. Stub or placeholder READMEs may
default to rewrite after stating that assessment. Detail:
[`../workflows/planning.md`](../workflows/planning.md).
