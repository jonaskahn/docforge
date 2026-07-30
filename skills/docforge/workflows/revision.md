# Revision

Owns: `--resume`, `--status`, `--revise all`, `--revise <area>`,
`--revise flow`, flow-index organization, provisional flow derivation, and
single-document update / refresh.

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
3a. **Suitable missing audiences** — when step 2 or 3 finds missing, new, or
   updated documents, collect their catalog `selection.audiences` that are not
   already on the manifest. Before writing, prompt via
   [`intake.md`](intake.md) Output audience: show all seven catalog audiences,
   pre-check current ∪ suitable missing (with a one-line reason per suitable
   missing, e.g. which `ba_*` / `po_*` / `agents_*` docs they unlock), and let
   the user confirm or **add more**. Apply for `--revise all`, `--revise
   <area>`, `--revise flow`, and any natural-language revise that rediscovers
   docs. Do not silent-add audiences.
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

## Commands

- `--resume`: run `migrate_metadata` when needed, load the version-3.1
  manifest, and continue the first non-complete, non-skipped document in write
  order. Proceed to [`writing.md`](writing.md) for that document.
- `--status`: print manifest state only.
- `--revise all` / `--revise <area>`: run `migrate_metadata` when needed, then
  apply the revise meaning above in scope — including the suitable-missing-
  audiences prompt (step 3a) after detect/catalog finds missing, new, or
  updated docs. If the manifest has no audiences, run the full audience
  multi-select.

  ```sh
  python scripts/check_staleness.py \
    --manifest <repo>/.docforge/manifest.json \
    --sync-provenance --json
  ```

  Re-ground `PARTIAL` sections; fully re-ground `UNTRACKED`. Re-detect and
  add missing / newly selected documents. Refresh big-picture and connection
  surfaces. Preserve verbatim only sections that are both `FRESH` **and**
  unaffected by new flows, new docs, or new connections in this revise.

## Update one document

Natural-language **update** or **refresh** of a **named** document uses this
path — not full revise rediscovery.

1. Run `migrate_metadata` when needed.
2. Scan only that document:

   ```sh
   python scripts/check_staleness.py \
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

## `--revise flow`

Natural-language **revise flow** always runs the **full** flow pipeline below.
It is not a blob-only pass. New flow connections force re-ground of existing
flow docs and big-picture surfaces even when their cited `git_blob` values are
still `FRESH`.

1. Run `migrate_metadata` when needed, then precheck `--need flow`.
2. Run `flow_index revise` to re-harvest candidates (with community-label and
   near-candidate dedup), upsert every row into `.docforge/flow-index.json`
   (schema 1.1), set non-documented/non-skipped rows to `placeholder`, create
   stub markdown **only for main-priority standalone** placeholders, prune
   orphan deferred / member / index-only scaffolds, and emit compact
   `.docforge/tmp/communities.md` when a GitNexus export is present. When this
   harvest (or later step 7) introduces missing / new flow-related docs, run
   the suitable-missing-audiences prompt (step 3a) before writing — e.g.
   Coding agents when `agents_flow` or other agent-context flow docs are
   newly selected.
3. Run `flow_index organize emit`, have the agent write
   `.docforge/tmp/flow-organization.json` (descriptive names, families,
   composition), and `flow_index organize apply` before deep-dive analysis.
4. Build an analysis pack from main-priority **standalone** flow-index rows,
   the compact communities summary, and (when no native flow graph)
   `derive_flow_graph prepare` context; the agent/LLM analyzes those
   standalone mains only into `.docforge/tmp/flow-analysis.json`, then runs
   `derive_flow_graph write` when a provisional graph is required. Full
   derivation reasoning:
   [`../references/graph/flow-derivation.md`](../references/graph/flow-derivation.md).
5. For each main-priority standalone flow (NOTICE first; pause in review mode,
   or continue under `--auto-accept`):
   - **New** main standalone → full write via [`writing.md`](writing.md).
   - **Existing** documented flow → re-ground for harvest / organization /
     connection changes; use `check_staleness --document` to limit *source*
     rework to `PARTIAL` / `UNTRACKED` sections, but still update connection,
     composition, and cross-link sections when the flow index or neighbors
     changed, even if blobs are `FRESH`.
6. Refresh the big picture: render `docs/flows/README.md`, and update any
   selected overview / index docs whose flow counts or links changed
   (for example `system-overview` when selected).
7. Add any other missing flow-related dynamic documents required by the
   current catalog selection and write them in `write_order`.

Distinct from `--revise <area>`, which does not re-harvest the flow index but
still applies the revise meaning (staleness, missing docs, big picture,
connections) inside that area.
