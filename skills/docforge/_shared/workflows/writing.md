# Writing

Owns: the per-document execution card, evidence retrieval, scaffolding,
provenance stamping, status transitions, mechanical linting, the independent
audit, and continuing an incomplete run (intake goal or plain language — there
is no `--resume` flag).

## Continue incomplete run

When the user chooses Resume in intake or asks to continue an incomplete
documentation run: run `migrate_metadata` when needed, load the version-3.1
manifest, and continue the first non-complete, non-skipped document in write
order. Then follow **Write one document** below for that document. May combine
with `--auto-accept`.

## 4. Write one document

For the next document in `write_order`:

1. Check every capability in its `requires` list.
2. Resolve its route in one call:

   ```sh
   python runtime/cli/python/query_catalog.py --route <id>
   node runtime/cli/js/query_catalog.js --route <id>
   # bun  runtime/cli/js/query_catalog.js --route <id>
   # deno run -A runtime/cli/js/query_catalog.js --route <id>
   ```

   Read its content contract (`contract`), then its optional `instruction`
   for writing craft. Select and author any visual using
   [`../references/illustration.md`](../references/illustration.md).
3. Materialize that document and selected ancestor indexes:

   ```sh
   python runtime/cli/python/scaffold_docs.py \
     --repo <repo> --manifest <repo>/.docforge/manifest.json \
     --document <id>
   node runtime/cli/js/scaffold_docs.js \
     --repo <repo> --manifest <repo>/.docforge/manifest.json \
     --document <id>
   # bun / deno run -A against runtime/cli/js/scaffold_docs.js with the same flags
   ```

4. Set it `in_progress`, re-ground every required claim, replace all scaffold
   markers and provenance tokens, and stamp complete provenance 2.0. For a
   large repository, the writer may dispatch `docforge-ground` to gather
   candidate `path` / `role` / `git_blob` evidence off-thread; it must verify
   every candidate and stamp provenance itself. The default is inline writer
   grounding:

   - One provenance `sections[]` entry per Markdown heading that makes claims;
     `id` is that heading's anchor.
   - Each claim cites at least one repository-relative `path` with `role`
     (`code`, `config`, `manifest`, `doc`, `test`, or `history`) and
     `git_blob` = the SHA-1 of `blob <len>\0` + file bytes (same value as
     `git hash-object <path>` and `check_staleness`'s blob helper).
   - Empty `sections: []` is valid only while the document is `planned` or a
     fresh scaffold; lint rejects empty sections for written documents.
   - Filled example and field rules:
     [`../references/provenance-tracking.md`](../references/provenance-tracking.md).

   After an update that touched only some sections, restamp those sections'
   sources and leave FRESH sections' provenance rows unchanged.
5. Set it `generated`.
6. Run the document linter and any audit-profile-specific mechanical checks.
7. Independently audit it (below).
8. Record the result:

   ```sh
   python runtime/cli/python/manage_manifest.py audit \
     --repo <repo> --id <id> --mode subagent \
     --verdict PASS --report .docforge/audits/<id>.md
   node runtime/cli/js/manage_manifest.js audit \
     --repo <repo> --id <id> --mode subagent \
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
passing `subagent` or `cold-pass` audit record.

## 5. Independent audit

When supported, dispatch the `docforge-audit` fresh artifact-only subagent.
Give it the artifact, its catalog contract, target depth, relevant quality
checks, and cited sources—no writer reasoning. When subagents are unavailable,
perform a separate cold, artifact-only pass and record `mode: cold-pass`.
Mechanical checks alone never produce a completion verdict. Full audit procedure:
[`../references/document-audit.md`](../references/document-audit.md).

Independent artifact-only audits may run concurrently, but their manifest
results are recorded serially by the orchestrator as required by
[`../references/parallel-execution.md`](../references/parallel-execution.md).

Next: once every selected document passes individually, proceed to
[`validation.md`](validation.md) for the whole-tree gate.
