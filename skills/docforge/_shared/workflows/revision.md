# Revision

Owns: `/docforge-revise` (`flow` | `<area>` | `all`), its flags
(`--plan-only`, `--auto-accept`, `--no-dashboard`), the revise side of the
flow pipeline, document retirement, current-template conformance, and
single-document update / refresh.

## What revise means

**Revise** is a structural refresh of the plan and tree, not a blob-only
touch-up. A revise run (all, area, or flow) applies every step below that
falls in scope:

1. **Update obsolete documents** — sync provenance and re-ground every
   blocking section; `COSMETIC` never blocks. Verdicts are defined in
   [`validation.md`](validation.md) "Manifest and provenance"; per-document
   mechanics are in Update one document below.
1a. **Upgrade contract-drifted documents** — a document whose catalog
    `contract_revision` changed is set `in_progress` with its audit cleared
    by reconcile, even when its source provenance is `FRESH`. Re-ground the
    affected sections (section READMEs: self-introduction, at-a-glance,
    scope and boundaries, start-here reading paths, child map, related
    sections, empty state), preserve valid prose, lint, audit,
    complete it. A second revise is idempotent once the current revision is
    complete.
1b. **Enforce current template conformance** — for every in-scope written
    document, the **newest template is the authority**. Fetch the document's
    current contract, instruction, and template via
    `query_catalog.{py,js} --route` (`contract`, `instruction`,
    `template_file`; see
    [`../runtime/catalog/README.md`](../runtime/catalog/README.md)), then
    compare the written document against the newest template's structure,
    format, and content requirements: required headings and their order,
    section granularity, tables and code blocks, typed-token vs
    concrete-value discipline, and the contract's keep-out boundaries.
    Document is old — structure deviates from the newest template, the
    template itself changed (with or without a `contract_revision` bump), or
    a required section is missing — the document is planned `rewrite` to the current
    template, even when its source blobs are `FRESH`. Never preserve an old
    structure and only patch stale content: the current template is the
    structure the document must have. Apply before source rework so a
    rewritten document is re-grounded once, not twice.
1c. **Apply layout switches** — a compact↔standard switch is a selection
    change: it flows through the selection-change preview and Retirement,
    never its own mechanism.
    - **standard → compact**: the group's component documents are `merge`d
      into the target file — scaffold the merged entry, migrate valid prose
      from each member using the Template rewrite mechanics, then `retire`
      the now-empty component files.
    - **compact → standard**: the merged file is `split` — scaffold the
      component entries, migrate each section's prose to its component,
      then `retire` the merged file.
    - Step 1b resolves templates by the manifest's own document id, so a
      compact project routes to composed compact contracts and a standard
      project to standard ones. Only the transition above is extra work.

    Dynamic instances move with the same two verbs:
    - **standard → compact**: each `docs/flows/<slug>.md`, ADR, concept,
      runbook becomes a `##` section on its group's merged entry, in
      `compact_order`, and its file is retired; instances past
      `COMPACT_DYNAMIC_CAP` become rows in the merged file's candidate
      matrix and their prose is retired with the file, never discarded
      silently — report them in the preview.
    - **compact → standard**: each section descriptor on `compact_members`
      (`{id, slug, title}`) is re-added with
      `manage_manifest add --type <id> --id <slug>` and its prose migrated
      to the new file. A matrix row has no prose to migrate; it becomes a
      stub, exactly as a deferred candidate does on a fresh standard run.

2. **Add documents from detect / catalog** — re-run profile detection and
   condition evidence when needed; select newly evidenced static and
   dynamic types; add them to the manifest in `write_order`. The same
   detect run re-derives project scale from the gate pack's `scale` field
   (see step 2a).
2a. **Re-derive scale / layout** — compare the gate pack's detected class
    and suggested layout with `project.scale` per
    [`intake.md`](intake.md) "Revise selection changes": a `detected`
    decision that drifted → surface as a recommended change in the
    confirmation summary; a `user` or `migration` decision → report the
    drift as a fact, change nothing unless the user explicitly asks
    (`migration` marks a legacy backfill to `layout: standard`;
    `detected_layout` records what detection would have said).
    Confirmed change → `manage_manifest.{py,js} reconcile
    --scale-class` / `--layout`; class-only changes are a plain record
    update, layout changes flow through the annotated tree and
    Retirement as in step 1c.
3. **Fill missing documents** — any selected catalog type, new
   instruction, or contract that now requires a file and has no manifest
   entry is planned and written via [`writing.md`](writing.md). New craft
   instructions that demand additional files are in scope.
3a. **Suitable missing audiences** — when step 2 or 3 finds missing, new,
    or updated documents, collect their catalog `selection.audiences` and
    prompt via [`intake.md`](intake.md) "Output audience" before writing;
    never silent-add audiences.
4. **Update the big picture** — refresh owning indexes and overview docs
   affected by adds or rewires (e.g. `docs/README.md`, area READMEs,
   `docs/flows/README.md`, `system-overview` when selected) so tree and
   navigation stay coherent.
5. **Add connections** — wire cross-links, flow-index composition /
   families, and related-document pointers so new or reorganized flows and
   docs are never left as orphans; the per-document wiring is owned by
   [`writing.md`](writing.md) "Write one document" (step 10).
6. **Do not treat `FRESH` as a hard skip when structure changed** — if new
   flows, new documents, or new connections touch a document's role in the
   tree, re-ground the affected connection / overview sections even when
   recorded source blobs still match. Blob freshness proves cited source
   files are unchanged; it does not prove the document's place in the
   documentation graph is still correct. The same holds for illustration
   coverage: a `FRESH` document missing any view its `illustration_views`
   declares must gain that view on this revise — blob freshness does not
   prove the document answers every reader question its type owes.
7. **Triage unmanaged documents** — detect foreign docs and run the triage
   exactly as owned in
   [`../references/docs-tree.md`](../references/docs-tree.md) "Unmanaged
   documents"; the archive move is a file operation, so it is separately
   approved and never runs under `--auto-accept`. Already-recorded paths
   are baseline facts: never re-asked, never added to the plan, scaffold,
   or manifest. The proposals join this revise's confirmation summary
   (below).

**Ordering for `/docforge-revise all`:** steps 1–7 run first (migration,
staleness sync, template enforcement, detect/catalog, missing docs,
suitable-missing-audiences, big picture, connections, unmanaged triage),
then the flow pipeline with its mandatory gate (below), then the
annotated plan tree and writing. The flow gate still precedes the first
document write — the same write-start position the gate holds on a fresh
run.

The flow pipeline and the revise steps overlap at three points; on `all`
each is performed **once**, by the step that owns it:

- the **annotated plan tree / execution-mode checkpoint** — shown once,
  after the flow gate has settled which flows are in, so a single tree
  covers both the catalog delta and the flow delta;
- the **big-picture refresh** (`docs/flows/README.md` render, overview and
  index docs whose flow counts or links changed) — folded into step 4;
- **missing flow-related dynamic documents** — folded into step 3.

The flow pipeline contributes its precheck, harvest, organize, analyze,
gate, and writes; it does not open a second tree or a second big-picture
pass.

**Update / refresh of one named document** is the minimal exception:
blob-first, no rediscovery, unless that document is untracked or deviates
from the current template (step 1b).

### Template rewrite mechanics

A template rewrite runs in one pass per document:

1. Scaffold the **newest** template for the document
   (`scaffold_docs.{py,js} --document <id>`; see
   [`../runtime/documents/README.md`](../runtime/documents/README.md)) —
   never the old one.
2. Migrate still-valid prose into the matching new sections; drop obsolete
   sections and outdated formats; adopt every new required section. When a
   dropped section held an illustration that no longer fits the new
   template's illustration budget, check
   [`../references/illustration.md`](../references/illustration.md)'s
   table-vs-diagram guidance before treating its information as obsolete —
   recasting the same facts as a table in the matching new section is a
   valid migration outcome, not just verbatim-move-or-drop.
3. Re-ground the rewritten document from evidence (one section per claim
   heading), replace scaffold markers and typed tokens, then run the
   mechanical gate (`lint_document.{py,js}` with the contract's
   required-heading set), the independent audit, and complete it.

The newest template decides the result. A rewritten document that still
carries the old structure, format, or content has not been rewritten — fix
it before moving on.

## Questions revise asks

Revise always **stops and asks first** — never proceed on silent defaults.
A **bare** `/docforge-revise` is the one exception: metadata-only
migration, asks nothing (see Commands below). Every other revise invocation
presents a discovery brief and a **delta-aware** question set before any
scope decision, detection, or writing — never a reflexive full re-ask.

`migrate_metadata.{py,js}` is the one thing that runs before the brief —
a mechanical, idempotent schema prerequisite, not a decision
([`validation.md`](validation.md) "Manifest and provenance"). The brief
reports the manifest's own tier and profiles, so the record must be at the
current schema before it can be read out. Nothing else — no detection, no
reconcile, no scaffold, no write — precedes the question set.

Revise uses the same two-turn split as a fresh start
([`intake.md`](intake.md) "Turn structure"): **Turn 1** asks Scope, Layout,
and Flow mode, **Turn 2** asks Tier, Profiles, Output audience, and
Execution mode. Never present layout in the same turn as tier, profiles, audiences,
or execution mode; open Turn 2 only after Turn 1 is answered.

**Scope** (Turn 1) — `flow`, `<area>`, or `all` (pre-checked from
invocation; asked only for natural-language revise requests, never for a bare `/docforge-revise`).

**Flow mode** (Turn 1, single-select, only when the scope is `flow` or
`all` — or a natural-language revise that touches flows; `<area>` revise
never re-harvests and never asks):

- **Re-analyze flows** — full re-harvest from the provider plus a fresh
  deep analysis of every candidate. Recommended when the repository moved
  materially since the last flow pass.
- **Reuse existing flow analysis** — re-harvest only to catch **missing**
  candidates; stored summaries, organization, and analyses are reused for
  everything already indexed. Missing candidates are explicitly analyzed
  before the selection prompt.

The answer governs steps 2–4 of `/docforge-revise flow` below. A reply
that leaves it unanswered → one flow-mode-only follow-up. **Never**
proceed with a silently assumed mode.

**Flow selection is a mandatory gate — `--auto-accept` never waives
it.** The add/remove/update selection prompt is always
shown and always awaited, exactly like the intake confirmation: which
flows become documents is a scope decision, and the user must choose to
go ([`../references/graph/flow-derivation.md`](../references/graph/flow-derivation.md)
"Selection gate and write-back"). Only the execution-mode pauses around
the gate honor the flag.

[`intake.md`](intake.md) "Scope intake" owns the exact per-dimension rule —
which of Scope, Tier, Profiles, Output audience, and Execution mode get
asked versus reported as an unchanged baseline fact. Two exceptions live
there and apply here unchanged:

- **Tier-naming.** `/docforge-revise all`, or any invocation that names a
  tier, always shows the tier control and the selection-change preview
  below, even with no delta.
- **Execution mode.** Skipped only when the invocation already supplies
  `--plan-only` or `--auto-accept`.

After Turn 2, display one confirmation summary ([`intake.md`](intake.md))
covering every dimension, changed or unchanged. Wait for explicit
confirmation before continuing — required even when every dimension
resolves unchanged. The summary answers only what is actually in question.

The **unmanaged-document triage** (step 7) joins that same summary when
this revise finds foreign docs: one line per file with the proposed action
(keep self-managed is the recommended default; archive is listed as a
change requiring approval). Same stop-and-ask mechanics — never applied
silently, and `--auto-accept` never authorizes the archive move.

### Applying the answers to the manifest

First-time answers are stored in manifest metadata (`project.tier`,
`project.profiles`). Revise displays those current values separately and
lets the user request only changes: change tier, add selections, remove
selections. Anything missing or newly applicable is generated as a
recommended add action. Apply the confirmed result mechanically with
`manage_manifest.{py,js} reconcile` (see
[`../runtime/manifest/README.md`](../runtime/manifest/README.md)):

```sh
python3 runtime/cli/python/manage_manifest.py reconcile --repo <repo> \
  [--tier <spine|diligence|portfolio>] \
  [--scale-class <small|medium|large>] [--layout <compact|standard>] \
  [--shape <id> ...] [--platform <id> ...] [--framework <id> ...] \
  [--concern <id> ...] [--audience <id> ...]
```

Rules:

- Omitted dimension flags keep the manifest's current values, including the
  scale record — reconcile only rewrites `project.scale` when
  `--scale-class` or `--layout` is passed.
- Pass `--audience none` (or the matching dimension flag with `none`) to
  clear that dimension entirely.
- A scale flag records `decided_by: "user"` with fresh `signals` and the
  detected class preserved as `detected_class`.
- Changing the tier **to** `portfolio` on a compact manifest also changes
  the layout to `standard` — compact covers Spine and Diligence only
  ([`../references/docs-tree.md`](../references/docs-tree.md) "Compact
  layout"). Reconcile records `decided_by: "tier-constraint"`, re-plans the
  folded members, and reports the merged entries as removed or retire
  candidates. Show both the tier change and the layout change in the
  selection-change preview; never apply the layout change silently. An
  explicit `--layout compact` with `--tier portfolio` is rejected outright.
- Newly applicable documents are added as `planned` in write order.
- Planned documents that are no longer applicable are removed from the
  plan (`removed-planned` in the report).
- Written, skipped, and dynamic documents are always preserved — reconcile
  never deletes content or dynamic instances. **Written** static documents
  that fall out of the selection are reported as `retire` candidates (never
  touched by reconcile itself); retirement is a separate, explicitly
  approved step after the delta is confirmed — see Retirement below.
- Ancestor indexes are recomputed with the new selection.
- Kept documents have their catalog-owned metadata refreshed (title,
  template, instruction, depth, write order, audit profile, requires);
  written documents whose `contract_revision` drifted are demoted to
  `in_progress` with cleared audits and reported under `contract-updated` —
  re-ground them as in step 1a even when source blobs are `FRESH`.
- `--group` behaves like every other dimension flag: omitted keeps the
  manifest's stored scope, `--group none` clears it back to every group.
  **`/docforge-revise <area>` never passes `--group`** — see "Area scope
  is not group scope" below.
- The command prints the delta — a counts summary first (`3 add, 2
  retire`) so the shape of the change is legible, then the detail lines
  (tier, profiles, added, removed-planned, retire, contract-updated, kept)
  and the annotated plan tree; then continue with `scaffold_docs.{py,js}
  --dry-run --revise` and the writing workflow.

### Area scope is not group scope

`project.groups` is a **persistent scope**: narrowing it means those areas
are no longer part of this repository's documentation, so every written
document in a dropped area correctly becomes a `retire` candidate.
`<area>` is a **transient work filter**: it narrows which in-scope
documents this run writes and nothing else.

`/docforge-revise architecture` passing `--group architecture` to
reconcile would nominate the entire rest of the written tree for
retirement. So it never does: reconcile runs with no `--group` (the
omitted-flag rule above keeps the stored scope), and only the write step
is narrowed. Only intake, or an explicit widen/narrow request, changes
`project.groups`.

Valid `<area>` values are the catalog group ids and their aliases, from
`query_catalog.{py,js} --groups`. An unknown area is an error that lists
the allowlist; it never falls back to a full-tree revise. `flow` and
`flows` are **reserved** for the flow pipeline (harvest → organize →
derive → write), which is strictly more than revising the `flows` group —
neither is an area.

`/docforge-revise agents` on a manifest with no agent documents offers the
repair rather than failing:

- `coding-agents` audience missing → offer to add it
  (`reconcile --audience coding-agents`).
- Audience present but `project.groups` excludes `agent-context` → offer
  to widen the scope (widening adds no retire candidates).
- Declined → stop with `nothing in scope for
'agents'`. Never add either silently.

### Agent-context revision

Agent-context isolation never changes with scope. Outputs remain
self-contained and zero-reference whether revised alone, alongside
human-facing documentation, or after the selected area set changes. The
catalog contract revision `2.23.0` therefore rewrites any older routed or
importing form through steps 1a and 1b without a conversion prompt.
Standard and compact layout switches remain content-preserving under the
normal split/merge mechanics.

## Annotated plan tree

Before any writing, revise (and fresh-start planning) displays the plan
tree with a per-document action comment, so the user sees exactly what
will happen:

- `add` — not planned yet, or planned with no file (will be scaffolded).
- `update` — file exists; changed sections will be re-ground.
- `rewrite` — full re-ground (provenance missing/unparseable, status is
  `in_progress` / `needs_review`, or structure / format / content deviates
  from the current template per step 1b). A template rewrite is annotated
  `rewrite (template)` in the tree so the user sees which documents are
  being moved to the newest template rather than patched.
- `unchanged` — fresh with valid provenance; re-checked only when a
  structural change touches it.
- `skip` — explicitly skipped.
- `retire` — **written** but no longer selected (tier downgrade, profile /
  audience removal, or a layout switch); the entry stays in the manifest
  and the file is moved or deleted by the approved retire step,
  destination shown per Retirement below.
- `removed-planned` — planned, never written; dropped from the plan.
- `split` — compact → standard layout: one merged file becomes its N
  component files.
- `merge` — standard → compact layout: N component files become one
  merged file.

Selected flows (main-priority after the selection gate) are listed under a `Flows:` section mapping each flow
to its document path (`docs/flows/<slug>.md`) with the same action
annotation. Compact layout: the path is the merged file's anchor instead
(`docs/flows.md#<slug>`), and a flow over `COMPACT_DYNAMIC_CAP` is listed
as a matrix row. Run it directly with `scaffold_docs.{py,js} --dry-run
--revise`.

## Retirement

Three selection changes retire documents, all sharing this one mechanism:
a **tier downgrade**, a **profile or audience removal**, and a
**compact↔standard layout switch**. `reconcile` reports every affected
written document as a `retire` candidate before anything moves; the
retirement itself is a separate step the user explicitly approves.

Two destinations, chosen per run:

- **Move to the git-ignored obsolete location (default)** —
  `.docforge/obsolete/<year>/` (same relative path below the year folder).
  `.docforge/` already has maintained ignore machinery, so nothing is
  added to the repository's own `.gitignore`; the location is outside
  `docs/`, so the dashboard and the audit's `unexpected` check skip it
  for free.
- **Delete** — the file is removed entirely. Offered as an explicit
  choice; never the default.

Apply an approved retirement mechanically:

```sh
python3 runtime/cli/python/manage_manifest.py retire --repo <repo> \
  --doc <id> [--doc <id> ...] --mode obsolete|delete [--dry-run]
```

Both modes are file operations: **always explicitly approved, never under
`--auto-accept`**, consistent with [`flags.md`](../flags.md) ("never
authorizes … file archive/deletion"). Reconcile itself still never deletes
content — retirement runs only after the delta is confirmed. The manifest
entry is kept with `status: retired`, `retired_at`, and (for `obsolete`)
the `retired_destination` path — history is preserved and a later revise
can report what happened and where the content went. A `retired` document
is excluded from the whole-tree gate's coverage expectations exactly like
a `skipped` one, and a later selection change that re-selects a retired
document returns it to `planned` for a fresh scaffold.

Distinct from `docs/_archive/<year>/`, which stays what it is: tracked,
audit-known, and used for unmanaged (user-authored) document triage.
Retired documents are Docforge-generated content leaving scope — a
different thing, hence a different destination.

## Commands

### `/docforge-revise`

| Invocation | Behavior |
|---|---|
| `/docforge-revise` | **Metadata-only migration**: upgrade the manifest to current schema/version via `migrate_metadata.{py,js}`. No scope question, no detection, no writing, no dashboard (see below) |
| `/docforge-revise all` / `/docforge-revise <area>` | Run `migrate_metadata.{py,js}` first (see [`validation.md`](validation.md) "Manifest and provenance"), then apply the revise meaning above in scope — including the suitable-missing-audiences prompt (step 3a) after detect/catalog finds missing, new, or updated docs. Manifest has no audiences → run the full audience multi-select. `all` additionally asks the flow mode question and runs the full flow pipeline from its `--need flow` precheck onward (see `/docforge-revise flow` below), in scope with everything else and with the overlaps merged per the Ordering note above; `<area>` never does. |
| `/docforge-revise flow` | Run `migrate_metadata.{py,js}` first, then the full flow pipeline (see below) |

### Bare `/docforge-revise` — metadata-only migration

A bare `/docforge-revise` (no scope argument) is the minimal, quiet path:
it only migrates/upgrades manifest metadata. Asks no questions, does no
detection or rediscovery, writes no documents, never starts the dashboard.

1. Run the read-only preview:
   `migrate_metadata.{py,js} --repo <repo> --dry-run`.
2. Migration is unconditional — upgrade to 3.10 / provenance 2.1; see
   [`validation.md`](validation.md) "Manifest and provenance" for the full
   version list, sidecar moves, scale-record backfill, and legacy
   re-registration mechanics; the `--dry-run` preview lists the moves
   before anything is written.
3. Manifest already current → report that nothing needed migrating and
   stop; optionally point at the scoped invocations (`/docforge-revise
   all`, `<area>`, `flow`) for a structural refresh.

`--plan-only` runs only step 1 and never applies; `--auto-accept` and
`--no-dashboard` have no effect on this path (there are no pauses and no
dashboard).

#### Flags (same as `/docforge`)

Definitions are owned by [`flags.md`](../flags.md); flags combine with a
scope argument, e.g. `/docforge-revise flow --plan-only`. Revise-specific
effects only:

| Flag | Effect on revise |
|---|---|
| `--plan-only` | Covers migrate, staleness sync, detect/catalog, the suitable-missing-audiences prompt, the flow gate when the scope re-harvests flows, and the structure update / dry-run tree. Stops before writing or re-grounding document bodies; the flow index and its main-standalone stubs are metadata and are still written |
| `--auto-accept` | The flow selection gate stays mandatory and the unmanaged-doc archive + retirement moves stay separately approved — see [`flags.md`](../flags.md) |
| `--no-dashboard` | No effect on a bare `/docforge-revise` — there is no dashboard on that path |

Because migration re-registers legacy manifests the same way as the bare
path ([`validation.md`](validation.md) "Manifest and provenance"), a
revise run over an old manifest re-grounds and audits the adopted
documents like any other written tree (steps 1 / 1a / 1b above).

The staleness sync runs `check_staleness.{py,js}` — canonical invocations
and verdict meanings in [`validation.md`](validation.md) "Manifest and
provenance". Unless `--plan-only`, it drives step 1 (re-ground what is
blocking), step 3 (add missing / newly selected documents), and steps 4–6
(refresh big-picture and connection surfaces). Step 6 is the one that
overrides freshness: a `FRESH` or `COSMETIC` section is preserved verbatim
only when this revise's new flows, documents, and connections leave it
untouched.

## Update one document

Natural-language **update** or **refresh** of a **named** document uses
this path — not full revise rediscovery.

**Unmanaged documents.** Named document has no manifest entry (or is
recorded in `project.unmanaged_docs`) → it is an unmanaged doc: update
its content in place with the normal grounding and writing quality
([`writing.md`](writing.md) craft, without a manifest entry), but
**never** add it to the manifest, never stamp Docforge provenance, and
keep (or record) it in `project.unmanaged_docs` — the file keeps
belonging to the user. File is foreign and not yet recorded → ask the
keep-self-managed / archive triage first
([`../references/docs-tree.md`](../references/docs-tree.md) "Unmanaged
documents") and apply it with `manage_manifest.{py,js} unmanaged`, then
update the doc wherever it now lives.

1. Run `migrate_metadata.{py,js}` first — see [`validation.md`](validation.md)
   "Manifest and provenance" (unconditional, even for a single-document
   update).
2. Scan only that document — `check_staleness.{py,js}` with
   `--document <id|path> --sync-provenance --json` (canonical
   invocations: [`validation.md`](validation.md) "Manifest and
   provenance").
3. Branch on the result (verdict meanings:
   [`validation.md`](validation.md) "Manifest and provenance"):
   - all `FRESH` or `COSMETIC` → report that recorded sources are
     unchanged. Do not rewrite
     unless the user also asked for wording edits unrelated to source
     drift, the document's structure / format / content deviates from
     the current template (step 1b) — then rewrite to the template — or
     the document's declared `dominant_form` warrants a visual the file
     does not carry (below).
   - blocking `PARTIAL` (`STALE` / `MISSING` / `NO_BLOB`) → open only
     the listed section ids and their source files; re-ground those
     sections; keep every `FRESH` and `COSMETIC` section verbatim;
     restamp provenance for changed sections (see
     [`writing.md`](writing.md) stamp recipe and
     [`../references/provenance-tracking.md`](../references/provenance-tracking.md)).
   - `UNTRACKED` / empty sections / `UNPARSEABLE` → full re-ground and
     stamp via [`writing.md`](writing.md).
4. **Illustration coverage is structural, never a blob check** — in every
   branch above, verify each view the manifest entry's
   `illustration_views` declares against the file, **by form**: a declared
   `sequenceDiagram` is not satisfied by a layout tree that happens to be
   present. Missing → author that view in its named section from the
   instruction's `## Illustration` block and `illustration.md`'s budget, in
   the same pass, without touching `FRESH`/`COSMETIC` section prose. A view
   marked `required: false` is authored only when its evidence exists. This
   is what makes an already-written, under-illustrated document gain the
   views it owes on the next revise.
5. **Re-expand source links** — run `link_sources.{py,js} --write` for the
   document (see [`writing.md`](writing.md)). Re-running re-pins every link
   to the current commit and re-validates every path and range, so a
   reference that a refactor invalidated surfaces here instead of 404ing
   for a reader. A document whose sources are `FRESH` still gets this: the
   commit moved even when the file did not.
6. Run mechanical lint, independent audit, and manifest status updates.

Graph precheck still applies when the document's `requires` list demands
it.

## `/docforge-revise flow`

Natural-language **revise flow** always runs the **full** flow pipeline
below. It is not a blob-only pass. New flow connections force re-ground
of existing flow docs and big-picture surfaces even when their cited
`git_blob` values are still `FRESH`. At `spine`, the pipeline still
harvests but stops at the matrix render — no gate, no selection prompt
([`../references/graph/flow-derivation.md`](../references/graph/flow-derivation.md)
"Flow pipeline").

The **flow mode question** is answered in Turn 1 — see "Questions revise
asks". The **flow selection gate** is mandatory ([`../flags.md`](../flags.md));
only the execution-mode pauses around the gate honor the flag.

Run the canonical pipeline — precheck → harvest/import → organize →
analyze → selection gate → apply → write → write-back → render — exactly as
[`../references/graph/flow-derivation.md`](../references/graph/flow-derivation.md)
"Flow pipeline" specifies (every command and flag, the analysis depth rule,
the prompt's contents and `--main-limit` budget, the `update`
promote/demote/decline mapping).

Revise differs from a fresh start in five places, and only these:

- **Migration first.** `migrate_metadata.{py,js}` runs before the
  pipeline's precheck, as on every revise path
  ([`validation.md`](validation.md) "Manifest and provenance").
- **The flow-mode answer selects the harvest verb.** Re-analyze →
  `flow_index.{py,js} harvest`, a full re-harvest whose rows supersede
  every stored analysis. Reuse → `flow_index.{py,js} revise`, which
  catches **missing** candidates only; existing rows keep their stored
  status, priority, organization, `summary`, and `written_at`.
- **The same answer selects analysis breadth.** Re-analyze → the full deep
  pack for main-priority standalone rows. Reuse → the deep pack only for
  missing candidates and for rows promoted from deferred during the
  prompt; everything else reuses its stored analysis. Deferred rows get
  summary-level context either way.
- **Per-row actions are add / remove / update**, not the fresh start's
  promote / demote / skip: **add** for missing or newly promoted
  candidates (analyzed first), **remove** for selected rows the user
  drops, **update** for documented flows whose `check_staleness` reports
  blocking sections or whose composition / connections changed. Unchanged
  rows are baseline facts, never re-asked.
- **Apply order is `revise` → `update` → `manage_manifest add`.** The
  re-harvest must land in the real index before `update` touches a row —
  `update` fails on an id the index has never seen. When the added
  documents include flow-related types the manifest's audiences do not
  cover, run the suitable-missing-audiences prompt (step 3a) before
  writing — e.g. Coding agents for `agents_flow`.

Writing the selected flows follows [`writing.md`](writing.md) in
`write_order`, with one revise-specific rule: an **updated** documented flow
limits source rework to its blocking / untracked sections
([`validation.md`](validation.md) "Manifest and provenance") but still
re-grounds connection, composition, and cross-link sections when the index
or its neighbors changed, even on `FRESH` blobs — and is rewritten to the
current `flow` template when its shape has drifted (step 1b), never
patched in place.

Distinct from `/docforge-revise <area>`, which does not re-harvest the
flow index, never asks the flow mode question, and still applies the
revise meaning (staleness, missing docs, big picture, connections)
inside that area.

## Completion

After the last document in scope passes its independent audit, run the
whole-tree gate and the dashboard auto-serve step exactly as a fresh-start
run does ([`validation.md`](validation.md) "Whole-tree gate" and
"Dashboard auto-serve"), including the compact-layout offer exception.
