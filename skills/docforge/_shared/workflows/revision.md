# Revision

Owns: `/docforge-revise` (`all` | `<area>` | `flow`), its flags
(`--plan-only`, `--auto-accept`), flow-index organization, provisional flow
derivation, and single-document update / refresh.

## What revise means

**Revise** is a structural refresh of the plan and tree, not a blob-only
touch-up. A revise run (all, area, or flow) does all of the following that
apply in scope:

1. **Update obsolete documents** — sync provenance and compare `git_blob`
   values; re-ground `PARTIAL` / `UNTRACKED` sections (see Update one
   document for the per-doc mechanics).
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

**Update / refresh of one named document** is the cheap exception: blob-first,
no rediscovery, unless that document is untracked.

## Questions revise asks

Revise always **stops and asks first**, using the interactive question pack owned by
[`intake.md`](intake.md) — never proceed on silent defaults. Before migration, detection, or writing,
revise presents a discovery brief and one combined question set ([`intake.md`](intake.md)):

1. **Scope** — `all`, `<area>`, or `flow` (pre-checked from invocation).
2. **Tier** — display the manifest tier and offer only `Change to <tier>` alternatives.
3. **Profiles** — shape, platform, framework, concern: display each current
   selection and offer `Add` / `Remove` actions; fresh detections are recommended
   `Add` actions.
4. **Output audience** — display current audiences and offer `Add` / `Remove`
   actions; suitable missing audiences are recommended `Add` actions with unlock
   reasons (see [`intake.md`](intake.md)).
5. **Execution mode** — review or Auto-accept.

Display one confirmation summary ([`intake.md`](intake.md)) and wait for explicit confirmation before continuing.

### Applying the answers to the manifest

The first-time answers are stored in manifest metadata (`project.tier`,
`project.profiles`); revise displays those current values separately and lets
the user request only changes: change tier, add selections, or remove
selections. Anything missing or newly applicable is generated as a recommended
add action. Apply the explicitly confirmed result mechanically with
`manage_manifest reconcile`:

```sh
python runtime/cli/python/manage_manifest.py reconcile --repo <repo> \
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
  never deletes content or dynamic instances.
- Ancestor indexes are recomputed with the new selection.
- The command prints the delta (tier, profiles, added, removed-planned, kept)
  and the annotated plan tree; then continue with `scaffold_docs --dry-run
  --revise` and the writing workflow.

## Annotated plan tree

Before any writing, revise (and fresh-start planning) displays the plan tree
with a per-document action comment, so the user sees exactly what will happen:

- `add` — not planned yet, or planned with no file (will be scaffolded).
- `update` — file exists; changed sections will be re-grounded.
- `rewrite` — full re-ground (provenance missing/unparseable, or status is
  `in_progress` / `needs_review`).
- `unchanged` — fresh with valid provenance; re-checked only when a structural
  change touches it.
- `skip` — explicitly skipped.

Main-priority flows are listed under a `Flows:` section mapping each flow to its
document path (`docs/flows/<slug>.md`) with the same action annotation. Run it
directly with `scaffold_docs --dry-run --revise`.

## Commands

### `/docforge-revise`

| Invocation | Behavior |
|---|---|
| `/docforge-revise` | Ask which scope: `all`, `<area>`, or `flow` |
| `/docforge-revise all` / `/docforge-revise <area>` | Run `migrate_metadata` when needed, then apply the revise meaning above in scope — including the suitable-missing-audiences prompt (step 3a) after detect/catalog finds missing, new, or updated docs. If the manifest has no audiences, run the full audience multi-select. |
| `/docforge-revise flow` | Full flow pipeline (see below) |

#### Flags (same as `/docforge`)

| Flag | Effect on revise |
|---|---|
| `--plan-only` | Run migrate, staleness sync, detect/catalog, suitable-missing-audiences prompt, and show the structure update / dry-run tree; stop before writing or re-grounding document bodies |
| `--auto-accept` | Display plans, trees, and results, then continue without routine conversational pauses; never authorizes install, graph build/refresh, manifest initialization, root `README.md` migration choices, file archive/deletion, or other side effects (see [`flags.md`](flags.md)) |

Flags combine with a scope argument, e.g.
`/docforge-revise flow --plan-only`.

```sh
python runtime/cli/python/check_staleness.py \
node runtime/cli/js/check_staleness.js \
# bun  runtime/cli/js/check_staleness.js \
# deno run -A runtime/cli/js/check_staleness.js \
  --manifest <repo>/.docforge/manifest.json \
  --sync-provenance --json
```

Unless `--plan-only`: re-ground `PARTIAL` sections; fully re-ground
`UNTRACKED`. Re-detect and add missing / newly selected documents. Refresh
big-picture and connection surfaces. Preserve verbatim only sections that are
both `FRESH` **and** unaffected by new flows, new docs, or new connections in
this revise.

## Update one document

Natural-language **update** or **refresh** of a **named** document uses this
path — not full revise rediscovery.

1. Run `migrate_metadata` when needed.
2. Scan only that document:

   ```sh
   python runtime/cli/python/check_staleness.py \
     --manifest <repo>/.docforge/manifest.json \
     --document <id|path> --sync-provenance --json
   ```

3. Branch on the result:
   - all `FRESH` → report that recorded sources are unchanged; do not rewrite
     unless the user also asked for wording edits unrelated to source drift.
   - `PARTIAL` → open only the listed section ids and their source files;
     re-ground those sections; keep every `FRESH` section verbatim; restamp
     provenance for changed sections (see [`writing.md`](writing.md) stamp
     recipe and
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

1. Run `migrate_metadata` when needed, then precheck `--need flow`.
2. When available, dispatch `docforge-flow` for its read-only harvest, rank,
   organization, and provisional-derivation proposal. It must use only a
   temporary/provisional workspace and return an advisory result; otherwise run
   the same stages inline. Use that result to show the structure update and
   honor the execution-mode tree checkpoint before changing the repository.
3. After that checkpoint, run `flow_index revise` to re-harvest candidates (with community-label and
   near-candidate dedup), upsert every row into `.docforge/flow-index.json`
   (schema 1.1), set non-documented/non-skipped rows to `placeholder`, create
   stub markdown **only for main-priority standalone** placeholders, prune
   orphan deferred / member / index-only scaffolds, and emit compact
   `.docforge/tmp/communities.md` when a GitNexus export is present. When this
   harvest (or later step 8) introduces missing / new flow-related docs, run
   the suitable-missing-audiences prompt (step 3a) before writing — e.g.
   Coding agents when `agents_flow` or other agent-context flow docs are
   newly selected.
4. Run `flow_index organize emit`, have the agent write
   `.docforge/tmp/flow-organization.json` (descriptive names, families,
   composition), and `flow_index organize apply` before deep-dive analysis.
5. Build an analysis pack from main-priority **standalone** flow-index rows,
   the compact communities summary, and (when no native flow graph)
   `derive_flow_graph prepare` context; the agent/LLM analyzes those
   standalone mains only into `.docforge/tmp/flow-analysis.json`, then runs
   `derive_flow_graph write` when a provisional graph is required. The main
   agent renders and writes the committed flow index only after the
   execution-mode tree checkpoint, preserving Review and `--auto-accept`
   behavior. Full
   derivation reasoning:
   [`../references/graph/flow-derivation.md`](../references/graph/flow-derivation.md).
6. For each main-priority standalone flow (NOTICE first; pause in review mode,
   or continue under `--auto-accept`):
   - **New** main standalone → full write via [`writing.md`](writing.md).
   - **Existing** documented flow → re-ground for harvest / organization /
     connection changes; use `check_staleness --document` to limit *source*
     rework to `PARTIAL` / `UNTRACKED` sections, but still update connection,
     composition, and cross-link sections when the flow index or neighbors
     changed, even if blobs are `FRESH`.
7. Refresh the big picture: render `docs/flows/README.md`, and update any
   selected overview / index docs whose flow counts or links changed
   (for example `system-overview` when selected).
8. Add any other missing flow-related dynamic documents required by the
   current catalog selection and write them in `write_order`.

Distinct from `/docforge-revise <area>`, which does not re-harvest the flow
index but still applies the revise meaning (staleness, missing docs, big
picture, connections) inside that area.
