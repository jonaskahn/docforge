# Writing

Owns: the per-document execution card, evidence retrieval, scaffolding,
provenance stamping, status transitions, mechanical linting, and the
independent audit.

## 4. Write one document

For the next document in `write_order`:

1. Check every capability in its `requires` list.
2. Resolve its route in one call:

   ```sh
   python scripts/query_catalog.py --route <id>
   ```

   Read its content contract (`contract`), then its optional `instruction`
   for writing craft. Select and author any visual using
   [`../references/illustration.md`](../references/illustration.md).
3. Materialize that document and selected ancestor indexes:

   ```sh
   python scripts/scaffold_docs.py \
     --repo <repo> --manifest <repo>/.docforge/manifest.json \
     --document <id>
   ```

4. Set it `in_progress`, re-ground every required claim, replace all scaffold
   markers and provenance tokens, and stamp complete provenance 2.0:

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
   python scripts/manage_manifest.py audit \
     --repo <repo> --id <id> --mode subagent \
     --verdict PASS --report .docforge/audits/<id>.md
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

Use a fresh artifact-only subagent when supported. Give it the artifact, its
catalog contract, target depth, relevant quality checks, and cited sources—no
writer reasoning. When subagents are unavailable, perform a separate cold,
artifact-only pass and record `mode: cold-pass`. Mechanical checks alone never
produce a completion verdict. Full audit procedure:
[`../references/document-audit.md`](../references/document-audit.md).

Independent artifact-only audits may run concurrently, but their manifest
results are recorded serially by the orchestrator as required by
[`../references/parallel-execution.md`](../references/parallel-execution.md).

Next: once every selected document passes individually, proceed to
[`validation.md`](validation.md) for the whole-tree gate.
