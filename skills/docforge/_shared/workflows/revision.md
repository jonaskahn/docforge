# Revision

Owns: `/docforge-revise` (`flow` | `<area>` | `all`), its flags
(`--plan-only`, `--auto-accept`, `--no-dashboard`), flow-index organization, provisional flow
derivation, and single-document update / refresh.

## What revise means

**Revise** is a structural refresh of the plan and tree, not a blob-only
touch-up. A revise run (all, area, or flow) does all of the following that
apply in scope:

1. **Update obsolete documents** — sync provenance and compare `git_blob`
   values; re-ground blocking `PARTIAL` (`STALE` / `MISSING` / `NO_BLOB`) /
   `UNTRACKED` sections (see Update one document for the per-doc mechanics). A
   raw-blob mismatch that's still `COSMETIC` — a source's recorded
   `git_blob_normalized` or `range_blob` still matches — needs no re-grounding.
1a. **Upgrade contract-drifted documents** — a document whose catalog
    `contract_revision` changed is set `in_progress` with its audit cleared by
    reconcile, even when its source provenance is `FRESH`. Re-ground the
    affected sections (for section READMEs: introduction, at-a-glance, scope,
    start-here, child map, empty state), preserve valid prose, lint, audit, and
    complete it. A second revise is idempotent once the current revision is
    complete.
1b. **Enforce current template conformance** — for every in-scope written
    document, the **newest template is the authority**. Fetch the document's
    current contract, instruction, and template via
    `query_catalog.{py,js} --route` (see
    [`../runtime/catalog/README.md`](../runtime/catalog/README.md))
    (`contract`, `instruction`, `template_file`), then compare the written
    document against the newest template's structure, format, and content
    requirements — required headings and their order, section granularity,
    tables and code blocks, typed-token vs concrete-value discipline, and the
    contract's keep-out boundaries. Whenever the document is old — its
    structure deviates from the newest template, the template itself changed
    (with or without a `contract_revision` bump), or a required section is
    missing — the document is planned `rewrite` to the current
    template, even when its source blobs are `FRESH`. Never preserve an old
    structure and only patch stale content: the current template is the
    structure the document must have, not a suggestion. Applied before source
    rework so a rewritten document is re-grounded once, not twice.
1c. **Apply layout switches** — a compact↔standard switch is a selection
    change like any other: it flows through the selection-change preview
    and Retirement, not its own mechanism. **standard → compact**: the
    group's component documents are `merge`d into the target file —
    scaffold the merged entry, migrate valid prose from each member using
    the Template rewrite mechanics, then `retire` the now-empty component
    files. **compact → standard**: the merged file is `split` — scaffold
    the component entries, migrate each section's prose to its component,
    then `retire` the merged file. Step 1b resolves templates by the
    manifest's own document id, so a compact project routes to composed
    compact contracts and a standard project to standard ones — the
    steady state is already correct; only the transition above is extra
    work.
2. **Add documents from detect / catalog** — re-run profile detection and
   condition evidence when needed; select newly evidenced static and dynamic
   types; add them to the manifest in `write_order`.
3. **Fill missing documents** — any selected catalog type, new instruction,
   or contract that now requires a file and has no manifest entry is planned
   and written (via [`writing.md`](writing.md)). New craft instructions that
   demand additional files are in scope.
3a. **Suitable missing audiences** — when step 2 or 3 finds missing, new, or updated
   documents, collect their catalog `selection.audiences` and prompt via [`intake.md`](intake.md)
   (Output audience) before writing; do not silent-add audiences.
4. **Update the big picture** — refresh owning indexes and overview docs
   affected by adds or rewires (for example `docs/README.md`, area READMEs,
   `docs/flows/README.md`, `system-overview` when selected) so the tree and
   navigation stay coherent.
5. **Add connections** — update cross-links, flow-index composition /
   families, and related-document pointers so new or reorganized flows and
   docs are wired into the graph of documentation, not left as orphans.
6. **Do not treat `FRESH` as a hard skip when structure changed** — if new
   flows, new documents, or new connections touch a document's role in the
   tree, re-ground the affected connection / overview sections even when
   recorded source blobs still match. Blob freshness only proves cited
   source files are unchanged; it does not prove the document's place in the
   documentation graph is still correct.
7. **Triage unmanaged documents** — detect foreign `.md` / `.mdx` files under
   `docs/` or `docs-portfolio/` that have no manifest entry and are not
   already recorded in `project.unmanaged_docs` (see
   [`../references/docs-tree.md`](../references/docs-tree.md) "Unmanaged
   documents"). Ask per file — **Keep self-managed** (recommended) or
   **Archive** to `docs/_archive/<year>/` — and apply mechanically with
   `manage_manifest.{py,js} unmanaged add` / `unmanaged archive` (archive is
   a file move: separately approved, never under `--auto-accept`).
   Already-recorded paths are baseline facts, never re-asked, and never
   added to the plan, scaffold, or manifest.

**Update / refresh of one named document** is the cheap exception: blob-first,
no rediscovery, unless that document is untracked or deviates from the current
template (step 1b).

### Template rewrite mechanics

A template rewrite runs in one pass per document:

1. Scaffold the **newest** template for the document
   (`scaffold_docs.{py,js} --document <id>`; see
   [`../runtime/documents/README.md`](../runtime/documents/README.md)), never
   the old one.
2. Migrate still-valid prose into the matching new sections; drop obsolete
   sections and outdated formats; adopt every new required section. When a
   dropped section held an illustration that no longer fits the new
   template's illustration budget, check
   [`../references/illustration.md`](../references/illustration.md)'s
   table-vs-diagram guidance before treating its information as obsolete —
   recasting the same facts as a table in the matching new section is a valid
   migration outcome, not just verbatim-move-or-drop.
3. Re-ground the rewritten document from evidence (one section per claim
   heading), replace scaffold markers and typed tokens, then run the
   mechanical gate (`lint_document.{py,js}` with the contract's
   required-heading set),
   the independent audit, and complete it.

The newest template decides the result. A rewritten document that still
carries the old structure, format, or content has not been rewritten — fix it
before moving on.

## Questions revise asks

Revise always **stops and asks first** — never proceed on silent defaults. A
**bare** `/docforge-revise` is the one exception: it is metadata-only
migration and asks nothing (see Commands below). For every other revise
invocation, before migration, detection, or writing, revise presents a
discovery brief and a question set that is **delta-aware**, not a reflexive
full re-ask of every dimension on every run.

**Scope** — `flow`, `<area>`, or `all` (pre-checked from invocation; asked
only for natural-language revise requests, never for a bare
`/docforge-revise`).

[`intake.md`](intake.md) "Scope intake" owns the exact per-dimension rule —
which of Scope, Tier, Profiles, Output audience, and Execution mode get
asked versus reported as an unchanged baseline fact, including the
tier-naming exception (`/docforge-revise all` or any invocation that names a
tier always shows the tier control and the selection-change preview below,
even with no delta) and the execution-mode exception (skipped only when the
invocation already supplies `--plan-only` / `--auto-accept`). Display one
confirmation summary ([`intake.md`](intake.md)), covering every dimension
whether changed or unchanged, and wait for explicit confirmation before
continuing — this still requires explicit confirmation even when every
dimension resolves unchanged; it answers only what is actually in question
instead of every dimension on every run.

The **unmanaged-document triage** (step 7) joins that same confirmation
summary when this revise finds foreign docs: one line per file with the
proposed action (keep self-managed is the recommended default; archive is
listed as a change requiring approval), resolved with the same stop-and-ask
mechanics — never applied silently, and `--auto-accept` never authorizes the
archive move.

### Applying the answers to the manifest

The first-time answers are stored in manifest metadata (`project.tier`,
`project.profiles`); revise displays those current values separately and lets
the user request only changes: change tier, add selections, or remove
selections. Anything missing or newly applicable is generated as a recommended
add action. Apply the explicitly confirmed result mechanically with
`manage_manifest.{py,js} reconcile` (see
[`../runtime/manifest/README.md`](../runtime/manifest/README.md)):

```sh
python3 runtime/cli/python/manage_manifest.py reconcile --repo <repo> \
  [--tier <spine|diligence|portfolio>] \
  [--shape <id> ...] [--platform <id> ...] [--framework <id> ...] \
  [--concern <id> ...] [--audience <id> ...]
```

Rules:

- Omitted dimension flags keep the manifest's current values.
- Pass `--audience none` (or the matching dimension flag with `none`) to clear
  that dimension entirely.
- Newly applicable documents are added as `planned` in write order.
- Planned documents that are no longer applicable are removed from the plan
  (`removed-planned` in the report).
- Written, skipped, and dynamic documents are always preserved — reconcile
  never deletes content or dynamic instances. **Written** static documents
  that fall out of the selection are reported as `retire` candidates (never
  touched by reconcile itself); retirement is a separate, explicitly
  approved step after the delta is confirmed — see Retirement below.
- Ancestor indexes are recomputed with the new selection.
- Kept documents have their catalog-owned metadata refreshed (title,
  template, instruction, depth, write order, audit profile, requires); written
  documents whose `contract_revision` drifted are demoted to `in_progress` with
  cleared audits and reported under `contract-updated` — re-ground them as in
  step 1a even when source blobs are `FRESH`.
- The command prints the delta — a counts summary first (`3 add, 2 retire`)
  so the shape of the change is legible, then the detail lines (tier,
  profiles, added, removed-planned, retire, contract-updated, kept)
  and the annotated plan tree; then continue with `scaffold_docs.{py,js}
  --dry-run --revise` and the writing workflow.

## Annotated plan tree

Before any writing, revise (and fresh-start planning) displays the plan tree
with a per-document action comment, so the user sees exactly what will happen:

- `add` — not planned yet, or planned with no file (will be scaffolded).
- `update` — file exists; changed sections will be re-ground.
- `rewrite` — full re-ground (provenance missing/unparseable, status is
  `in_progress` / `needs_review`, or structure / format / content deviates
  from the current template per step 1b). A template rewrite is annotated
  `rewrite (template)` in the tree so the user sees which documents are
  being moved to the newest template rather than patched.
- `unchanged` — fresh with valid provenance; re-checked only when a structural
  change touches it.
- `skip` — explicitly skipped.
- `retire` — **written** but no longer selected (tier downgrade, profile /
  audience removal, or a layout switch); the entry stays in the manifest and
  the file is moved or deleted by the approved retire step, destination shown
  per Retirement below.
- `removed-planned` — planned, never written; dropped silently from the plan.
- `split` — compact → standard layout: one merged file becomes its N
  component files.
- `merge` — standard → compact layout: N component files become one merged
  file.

Main-priority flows are listed under a `Flows:` section mapping each flow to its
document path (`docs/flows/<slug>.md`) with the same action annotation. Run it
directly with `scaffold_docs.{py,js} --dry-run --revise`.

## Retirement

Three selection changes retire documents, all sharing this one mechanism: a
**tier downgrade**, a **profile or audience removal**, and a **compact↔standard
layout switch**. `reconcile` reports every affected written document as a
`retire` candidate before anything moves; the retirement itself is a separate
step the user explicitly approves.

Two destinations, chosen per run:

- **Move to the git-ignored obsolete location (default)** —
  `.docforge/obsolete/<year>/` (same relative path below the year folder).
  `.docforge/` already has maintained ignore machinery, so nothing is added
  to the repository's own `.gitignore`, and the location is outside `docs/`,
  so the dashboard and the audit's `unexpected` check skip it for free.
- **Delete** — the file is removed entirely. Offered as an explicit choice;
  never the default.

Apply an approved retirement mechanically:

```sh
python3 runtime/cli/python/manage_manifest.py retire --repo <repo> \
  --doc <id> [--doc <id> ...] --mode obsolete|delete [--dry-run]
```

Both modes are file operations: **always explicitly approved, never under
`--auto-accept`**, consistent with [`flags.md`](../flags.md) ("never authorizes
… file archive/deletion"). Reconcile itself still never deletes content —
retirement runs only after the delta is confirmed. The manifest entry is
kept with `status: retired`, `retired_at`, and (for `obsolete`) the
`retired_destination` path — history is preserved and a later revise can
report what happened and where the content went. A `retired` document is
excluded from the whole-tree gate's coverage expectations exactly like a
`skipped` one, and a later selection change that re-selects a retired
document returns it to `planned` for a fresh scaffold.

Distinct from `docs/_archive/<year>/`, which stays what it is today: tracked,
audit-known, and used for *unmanaged* (user-authored) document triage.
Retired documents are Docforge-generated content leaving scope — a different
thing, hence a different destination.

## Commands

### `/docforge-revise`

| Invocation | Behavior |
|---|---|
| `/docforge-revise` | **Metadata-only migration**: upgrade the manifest to current schema/version via `migrate_metadata.{py,js}`. No scope question, no detection, no writing, no dashboard (see below) |
| `/docforge-revise all` / `/docforge-revise <area>` | **Always** run `migrate_metadata.{py,js}` first (schema + provenance sidecars, see [`validation.md`](validation.md) "Manifest and provenance"), then apply the revise meaning above in scope — including the suitable-missing-audiences prompt (step 3a) after detect/catalog finds missing, new, or updated docs. If the manifest has no audiences, run the full audience multi-select. |
| `/docforge-revise flow` | **Always** run `migrate_metadata.{py,js}` first (schema + provenance sidecars), then the full flow pipeline (see below) |

### Bare `/docforge-revise` — metadata-only migration

A bare `/docforge-revise` (no scope argument) is the cheap, quiet path: it
only migrates/upgrades manifest metadata. It asks no questions, does no
detection or rediscovery, writes no documents, and never starts the
dashboard.

1. Run the read-only preview:
   `migrate_metadata.{py,js} --repo <repo> --dry-run`.
2. Migration is unconditional (see [`validation.md`](validation.md) "Manifest
   and provenance"): upgrade manifest 3.5 / 3.4 / 3.3 (or
   3.2 / 3.1 / 3.0 / provenance 1.0) to 3.6 / 2.1 — seeding each document's
   catalog-owned `description` from the catalog `summary`, normalizing
   `provenance_storage` to `json`, the project's `unmanaged_docs`
   list (default empty), and the project's `scale` record
   (`decided_by: "detected"` when absent) — and re-register
   any pre-3.0 shape as 3.6
   (adopting legacy written documents as `generated` with provenance 2.1,
   demoting incomplete or unconvertible documents to `in_progress`), and
   print the migration report. The same run moves
   each section-provenance document's inline frontmatter into the folder
   sidecar (`.docforge/provenance/<folder>.json`) and strips it from the
   markdown, so generated files become pure content; the `--dry-run`
   preview lists the moves before anything is written.
3. When the manifest is already current, report that nothing needed
   migrating and stop — optionally point at the scoped invocations
   (`/docforge-revise all`, `<area>`, `flow`) for a structural refresh.

`--plan-only` runs only step 1 and never applies; `--auto-accept` and
`--no-dashboard` have no effect on this path (there are no pauses and no
dashboard). `migrate_metadata.{py,js}` is idempotent — re-running over an
up-to-date manifest is a clean no-op (scripts and README:
[`../runtime/manifest/README.md`](../runtime/manifest/README.md)).

#### Flags (same as `/docforge`)

| Flag | Effect on revise |
|---|---|
| `--plan-only` | Run migrate, staleness sync, detect/catalog, suitable-missing-audiences prompt, and show the structure update / dry-run tree; stop before writing or re-grounding document bodies |
| `--auto-accept` | Display plans, trees, and results, then continue without routine conversational pauses; never authorizes install, graph build/refresh, root `README.md` migration choices, file archive/deletion, or other side effects (see [`flags.md`](../flags.md)) |

Flags combine with a scope argument, e.g.
`/docforge-revise flow --plan-only`.

`migrate_metadata.{py,js}` also re-registers legacy manifests the same way
here as in the bare path above (see [`validation.md`](validation.md)
"Manifest and provenance" for the full adoption mechanics), so a revise run
over an old manifest re-grounds and audits the adopted documents like any
other written tree (steps 1 / 1a / 1b above). Both the bare and the scoped
paths stamp `.docforge/provenance/` sidecars and leave markdown
frontmatter-free; a document still carrying inline frontmatter from before
the sidecar store existed is moved in the same migration pass.

```sh
python3 runtime/cli/python/check_staleness.py \
node runtime/cli/js/check_staleness.js \
# bun  runtime/cli/js/check_staleness.js \
# deno run -A runtime/cli/js/check_staleness.js \
  --manifest <repo>/.docforge/manifest.json \
  --sync-provenance --json
```

Unless `--plan-only`: re-ground blocking `PARTIAL` (`STALE` / `MISSING` /
`NO_BLOB`) sections; fully re-ground `UNTRACKED`. Re-detect and add missing /
newly selected documents. Refresh big-picture and connection surfaces.
Preserve verbatim only sections that are `FRESH` or `COSMETIC` **and**
unaffected by new flows, new docs, or new connections in this revise.

## Update one document

Natural-language **update** or **refresh** of a **named** document uses this
path — not full revise rediscovery.

**Unmanaged documents.** When the named document has no manifest entry (or is
recorded in `project.unmanaged_docs`), it is an unmanaged doc: update its
content in place with the normal grounding and writing quality
([`writing.md`](writing.md) craft, without a manifest entry) but **never** add
it to the manifest, never stamp Docforge provenance, and keep (or record) it
in `project.unmanaged_docs` — the file keeps belonging to the user. When the
file is foreign and not yet recorded, ask the keep-self-managed / archive
triage first (see
[`../references/docs-tree.md`](../references/docs-tree.md) "Unmanaged
documents") and apply it with `manage_manifest.{py,js} unmanaged`, then update
the doc wherever it now lives.

1. **Always** run `migrate_metadata.{py,js}` first (schema + provenance
   sidecars; see [`validation.md`](validation.md) "Manifest and provenance") —
   unconditionally, even for a single-document update. An already-current
   manifest reports a clean no-op.
2. Scan only that document:

   ```sh
   python3 runtime/cli/python/check_staleness.py \
     --manifest <repo>/.docforge/manifest.json \
     --document <id|path> --sync-provenance --json
   ```

3. Branch on the result:
   - all `FRESH` or `COSMETIC` → report that recorded sources are unchanged (a
     `COSMETIC` source differs only in whitespace/line-endings or outside the
     cited range); do not rewrite unless the user also asked for wording edits
     unrelated to source drift, or the document's structure / format / content
     deviates from the current template (step 1b) — then rewrite to the
     template.
   - blocking `PARTIAL` (`STALE` / `MISSING` / `NO_BLOB`) → open only the
     listed section ids and their source files; re-ground those sections;
     keep every `FRESH` and `COSMETIC` section verbatim; restamp provenance
     for changed sections (see [`writing.md`](writing.md) stamp recipe and
     [`../references/provenance-tracking.md`](../references/provenance-tracking.md)).
   - `UNTRACKED` / empty sections / `UNPARSEABLE` → full re-ground and stamp
     via [`writing.md`](writing.md).
4. Run mechanical lint, independent audit, and manifest status updates.

Graph precheck still applies when the document's `requires` list demands it.

## `/docforge-revise flow`

Natural-language **revise flow** always runs the **full** flow pipeline below.
It is not a blob-only pass. New flow connections force re-ground of existing
flow docs and big-picture surfaces even when their cited `git_blob` values are
still `FRESH`.

1. **Always** run `migrate_metadata.{py,js}` first (schema + provenance
   sidecars), then precheck `--need flow`
   (`precheck_graph.{py,js}`, see
   [`../runtime/graph/README.md`](../runtime/graph/README.md)).
2. Run the read-only harvest, rank, organization, and provisional-derivation
   stages inline in a temporary/provisional workspace. Use the advisory result
   to show the structure update and honor the execution-mode tree checkpoint
   before changing the repository.
3. After that checkpoint, run `flow_index.{py,js} revise` to re-harvest
   candidates (with community-label and
   near-candidate dedup), upsert every row into `.docforge/flow-index.json`
   (schema 1.1), set non-documented/non-skipped rows to `placeholder`, create
   stub markdown **only for main-priority standalone** placeholders, prune
   orphan deferred / member / index-only scaffolds, and emit compact
   `.docforge/tmp/communities.md` when a GitNexus export is present. When this
   harvest (or later step 8) introduces missing / new flow-related docs, run
   the suitable-missing-audiences prompt (step 3a) before writing — e.g.
   Coding agents when `agents_flow` or other agent-context flow docs are
   newly selected. (`flow_index` scripts and README:
   [`../runtime/flows/README.md`](../runtime/flows/README.md))
4. Run `flow_index.{py,js} organize emit`, have the agent write
   `.docforge/tmp/flow-organization.json` (descriptive names, families,
   composition), and `flow_index.{py,js} organize apply` before deep-dive
   analysis.
5. Build an analysis pack from main-priority **standalone** flow-index rows,
   the compact communities summary, and (when no native flow graph)
   `derive_flow_graph.{py,js} prepare` context; the agent/LLM analyzes those
   standalone mains only into `.docforge/tmp/flow-analysis.json`, then runs
   `derive_flow_graph.{py,js} write` when a provisional graph is required.
   (`derive_flow_graph` scripts and README:
   [`../runtime/flows/README.md`](../runtime/flows/README.md)). The main
   agent renders and writes the committed flow index only after the
   execution-mode tree checkpoint, preserving Review and `--auto-accept`
   behavior. Full
   derivation reasoning:
   [`../references/graph/flow-derivation.md`](../references/graph/flow-derivation.md).
6. For each main-priority standalone flow (NOTICE first; pause in review mode,
   or continue under `--auto-accept`):
   - **New** main standalone → full write via [`writing.md`](writing.md).
   - **Existing** documented flow → re-ground for harvest / organization /
     connection changes; use `check_staleness.{py,js} --document` (see
     [`../runtime/manifest/README.md`](../runtime/manifest/README.md)) to
     limit *source*
     rework to blocking `PARTIAL` (`STALE` / `MISSING` / `NO_BLOB`) /
     `UNTRACKED` sections, but still update connection, composition, and
     cross-link sections when the flow index or neighbors changed, even if
     blobs are `FRESH`. Enforce current template conformance
     (step 1b): an old flow-document shape is rewritten to the current `flow`
     template, never preserved.
7. Refresh the big picture: render `docs/flows/README.md`, and update any
   selected overview / index docs whose flow counts or links changed
   (for example `system-overview` when selected).
8. Add any other missing flow-related dynamic documents required by the
   current catalog selection and write them in `write_order`.

Distinct from `/docforge-revise <area>`, which does not re-harvest the flow
index but still applies the revise meaning (staleness, missing docs, big
picture, connections) inside that area.

## Completion

After the last document in scope passes its independent audit, run the
whole-tree gate exactly as a fresh-start run does
([`validation.md`](validation.md) §7). Unless the invocation included
`--plan-only` or `--no-dashboard`, start the dashboard
(`dashboard.{py,js} start`, see
[`../runtime/dashboard/README.md`](../runtime/dashboard/README.md)),
wait for the healthy server, and report the `dashboard: <url>` line and URL
in the final response — a revised tree without a started, reported dashboard
is not a finished revise run. The compact-layout exception of
`validation.md` §8 applies unchanged: when `project.scale.layout ==
"compact"`, append the offer line instead of starting the dashboard, and an
explicit yes in the same turn runs the lifecycle unchanged.
