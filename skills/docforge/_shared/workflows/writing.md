# Writing

Owns: the per-document execution card, evidence retrieval, scaffolding,
provenance stamping, status transitions, mechanical linting, the independent
audit, and continuing an incomplete run (intake goal or plain language — there
is no `--resume` flag).

For each routed document, load `model_depth` from
`query_catalog.{py,js} --route` (see
[`../runtime/catalog/README.md`](../runtime/catalog/README.md)) and
apply the minimum rung in [`../references/model-depth-ladders.md`](../references/model-depth-ladders.md).
It is not a heading checklist: verify evidence, decisions, controls, interfaces,
and stopping conditions before requesting independent audit. Document lint also
validates illustration budgets and presentation-safe fences.

## Continue incomplete run

When the user chooses Resume in intake or asks to continue an incomplete
documentation run: always run `migrate_metadata.{py,js}` first (schema +
provenance sidecars; see
[`validation.md`](validation.md) "Manifest and provenance" — idempotent, a
clean no-op when current), load the
version-3.5
manifest, and continue the first non-complete, non-skipped document in write
order. Then follow **Write one document** below for that document. May combine
with `--auto-accept`.

## 4. Write one document

### Parallel fan-out of independent documents

When several pending documents are independent — no child-before-ancestor
ordering (§6) and no shared target file with a sibling worker — the
orchestrator may spawn sub-agents to write them in parallel. Spawn only when
it genuinely helps (large batches, many small independent documents);
otherwise keep the serial `write_order` loop. Contract
([`../references/parallel-execution.md`](../references/parallel-execution.md)):

- Before fan-out, the orchestrator scaffolds any shared ancestor indexes
  serially (indexes may exist before their children, §6), sets each document
  `in_progress` serially, and ensures `manifest["graph"]` is locked — self-healing
  with `set-graph --repo <repo>` first if it is somehow still absent. A worker
  never calls `precheck_graph` or `set-graph` itself and never selects or
  relocks a provider. On a Portfolio-collection root, an absent lock is
  expected and is never self-healed.
- Each worker receives its document card (route, `requires`, audience,
  presentation), evidence budget, one target artifact, and the session's
  locked graph provider/flow (`manifest["graph"]`, read-only). It runs the
  artifact portion of **Write one document** — route, materialize, re-ground
  (native provider first, whole-file read last, per step 4 above), provenance,
  mechanical lint — on **only its own artifact file**. It never calls
  `manage_manifest` and never edits shared indexes, other documents, the
  manifest, or the shared `.docforge/provenance/` folder sidecars (json
  storage mode) — the orchestrator owns those.
- Each worker returns a result contract (see parallel-execution.md): claims
  grounded with sources, unresolved gaps, lint findings, any defect it
  could not clear, and — in `json` storage mode — its stamped provenance
  payload (`id`/`title`/`description` + `docforge_provenance`) for the
  orchestrator to merge.

After all workers return, the orchestrator merges (including serially
merge-editing each worker's provenance payload into its folder sidecar when
`project.provenance_storage` is `json`), applies the status
transitions (`in_progress` → `generated`) serially per returned artifact, then
proceeds to the independent audit (§5), which may also run concurrently with
serial recording.

For the next document in `write_order` (serial mode):

1. Check every capability in its `requires` list. On a Portfolio-collection
   root (see [`../rules.md`](../rules.md) "Code-graph precondition"), a
   `code_graph` requirement is already resolved as "no source of its own" —
   never retry the graph gate or self-heal for that reason alone.
2. Resolve its route in one call:

   ```sh
    python3 runtime/cli/python/query_catalog.py --route <id> --audience <audience>
    node runtime/cli/js/query_catalog.js --route <id> --audience <audience>
   # bun  runtime/cli/js/query_catalog.js --route <id>
   # deno run -A runtime/cli/js/query_catalog.js --route <id>
   ```

    Apply the returned `primary_audience` and `presentation`, read its content
    contract (`contract`), then its optional `instruction` for writing craft.
    Use [`../references/code-presentation.md`](../references/code-presentation.md)
    and [`../references/evidence-presentation.md`](../references/evidence-presentation.md).
    Select and author any visual using
   [`../references/illustration.md`](../references/illustration.md).
3. Materialize that document and selected ancestor indexes:

   ```sh
   python3 runtime/cli/python/scaffold_docs.py \
     --repo <repo> --manifest <repo>/.docforge/manifest.json \
     --document <id>
   node runtime/cli/js/scaffold_docs.js \
     --repo <repo> --manifest <repo>/.docforge/manifest.json \
     --document <id>
   # bun / deno run -A against runtime/cli/js/scaffold_docs.js with the same flags
   ```

4. Set it `in_progress`, re-ground every required claim, replace all scaffold
   markers and provenance tokens, and stamp complete provenance 2.0. Re-ground
   in this order — native tool first, whole-file read last:
   1. Read the session's locked provider from `manifest["graph"]`
      (`.docforge/manifest.json`). Never re-detect and never re-ask; it was
      locked once, automatically, by `manage_manifest.{py,js} init` (see
      [`../references/graph/graph-sources.md`](../references/graph/graph-sources.md)
      "Session persistence").
   2. If `graph` is absent because no provider is ready **and this is not a
      Portfolio-collection root**, self-heal once with
      `manage_manifest.{py,js} set-graph --repo <repo>` (no other flags —
      automatic, registry-priority pick), then continue. On a
      Portfolio-collection root, `graph` legitimately stays absent for this
      repository; do not self-heal or retry.
   3. Dispatch the evidence question for each required claim through that
      provider's native interface first — `graph-sources.md`'s dispatch table
      (`codegraph_explore`, the GitNexus MCP tools/resources, or the relevant
      Understand Anything skill).
   4. Escalate to a direct file read only when the native query's returned
      evidence does not cover the claim, following the bounded ladder in
      [`../references/source-analysis.md`](../references/source-analysis.md):
      targeted symbol/region read, then keyword search within the candidate
      set, then whole-file only under its listed narrow conditions, then git
      history last. Never open a whole file as the first move.

   The writer gathers, verifies, and stamps all candidate `path` / `role` /
   `git_blob` evidence inline:
   - Storage mode decides where provenance lives — read it from
     `manifest["project"]["provenance_storage"]` (`json` is the default).
     In `json` mode the generated markdown carries **no frontmatter at all**;
     each document's public identity (`id`, `title`, `description`) and its
     `docforge_provenance` object live in one git-tracked sidecar per docs
     folder: `.docforge/provenance/<folder>.json` (e.g.
     `docs/architecture` → `.docforge/provenance/docs/architecture.json`,
     repo-root files → `root.json`). Stamp by merge-editing that folder's
     `files[<name>.md]` entry — never rewrite sibling entries. In `markdown`
     mode keep the legacy inline layout: public frontmatter `id`, `title`,
     `description` (a reader-facing one-liner, ≤ 160 chars, seeded from the
     catalog `summary` in the manifest) plus `docforge_provenance`; lint
     enforces a non-empty description for written documents.
   - One provenance `sections[]` entry per Markdown heading that makes claims;
     `id` is that heading's anchor.
     - Each claim records at least one repository-relative `path` with `role`
      (`code`, `config`, `manifest`, `doc`, `test`, or `history`) and
      `git_blob` = the SHA-1 of `blob <len>\0` + file bytes (same value as
       `git hash-object <path>` and `check_staleness.{py,js}`'s blob helper).
   - Always additionally stamp `git_blob_normalized` — the same blob-style
     SHA-1 but over the file's bytes after normalizing line endings
     (CRLF/CR -> LF), stripping trailing whitespace per line, and stripping
     trailing blank lines at EOF; omit the field only when the file is not
     UTF-8 text. When a claim cites a specific line range rather than the
     whole file, also record `evidence_range: {start, end}` (1-indexed,
     inclusive, same convention as the `path#Lstart-Lend` body-text evidence
     locators) and `range_blob` — the blob-style SHA-1 of just those lines'
     bytes. Compute all three with one command so every write turn hashes
     identically to what `check_staleness.{py,js}` recomputes later:
     `hash_evidence.{py,js} --repo <repo> --path <path> [--range <start>-<end>]
     --json`. Never hand-derive `git_blob_normalized` or `range_blob` — unlike
     `git_blob` (which matches ubiquitous `git hash-object`), these two have no
     standard-tool equivalent, so an ad hoc reimplementation risks silently
     diverging from what `check_staleness` recomputes later.
   - Empty `sections: []` is valid only while the document is `planned` or a
     fresh scaffold; lint rejects empty sections for written documents.
   - Filled example and field rules:
     [`../references/provenance-tracking.md`](../references/provenance-tracking.md).

   After an update that touched only some sections, restamp those sections'
   sources and leave FRESH sections' provenance rows unchanged.

   In `json` storage mode the folder sidecar is a **shared file** — parallel
   workers never write it (see §Parallel fan-out): each worker returns its
   stamped provenance payload in its result contract, and the orchestrator
   merge-edits the sidecar entries serially per returned artifact, together
   with the status transitions. Serial writers may merge-edit the sidecar
   directly.
5. Set it `generated`.
6. Run the document linter and any audit-profile-specific mechanical checks.
   For the `agents-kernel` output (`AGENTS.md`, a `SPECIAL_DOC_OUTPUTS` member
   that `lint_document.{py,js}` skips; see
   [`../runtime/documents/README.md`](../runtime/documents/README.md)), the
   mechanical gate is
   `lint_agents_kernel.{py,js} --file <path> --repo <root>` in place of
   `lint_document.{py,js}`.
7. Independently audit it (below).
8. Record the result:

   ```sh
   python3 runtime/cli/python/manage_manifest.py audit \
      --repo <repo> --id <id> --mode cold-pass \
     --verdict PASS --report .docforge/audits/<id>.md
   node runtime/cli/js/manage_manifest.js audit \
      --repo <repo> --id <id> --mode cold-pass \
     --verdict PASS --report .docforge/audits/<id>.md
   # bun / deno run -A against runtime/cli/js/manage_manifest.js with the same args
   ```

9. A passing artifact may transition to `complete`. A failed artifact becomes
   `needs_review`, then returns to `in_progress` for revision.

Status transitions are:

```text
planned → in_progress → generated → complete
                       ↘ needs_review → in_progress
```

`skipped` is explicit. `complete` is rejected unless the manifest contains a
passing `cold-pass` audit record.

## 5. Independent audit

After writing, start a separate cold, artifact-only pass with only the artifact,
its catalog contract, target depth, relevant quality checks, and cited sources;
do not carry over writer reasoning (mechanical lint, including the
`agents-kernel` carve-out, is step 6 above — not part of this pass). Record
`mode: cold-pass`. Mechanical checks alone never produce a completion verdict.
Full audit procedure:
[`../references/document-audit.md`](../references/document-audit.md).

Independent artifact-only audits may run concurrently, but their manifest
results are recorded serially by the orchestrator as required by
[`../references/parallel-execution.md`](../references/parallel-execution.md).

## 6. Bottom-up README closeout

Section READMEs are the top-down entry points of the tree, so they are
finalized **after** their child documents — never before. Ancestor indexes may
be scaffolded early (so the tree exists), but a README must not be grounded or
audited until the children it routes to are materialized.

After every selected document passes its independent audit, close out the
READMEs deepest-first:

```text
deepest collection READMEs (concepts, runbooks, decisions, migrations, epics)
→ area READMEs (architecture, product, engineering, operations, reference,
  security, contributing, agents, portfolio)
→ docs/README.md
→ root README.md
```

For each README-capable document (`folder-index`, `docs-index`, `ba-index`,
`po-index`, `portfolio-index`, `portfolio-decisions-index`, `decision-index`;
`flow-index` is rendered from the flow index first), re-ground it from
repository evidence and the completed children: self-introduction, at-a-glance,
scope and boundaries, start-here reading paths, child map with one reader
question per child, related sections, and an honest empty state when no child
is evidenced. Stamp provenance per heading, run the mechanical gate
(`lint_document.{py,js}` plus the `scaffold_docs.{py,js} --audit` README
child-coverage check),
then the independent audit, and record the result. Never restate child-owned
facts or link a child that is not selected and materialized.

Next: once every selected document passes individually, proceed to
[`validation.md`](validation.md) for the whole-tree gate.
