# Writing

Owns: the per-document execution card, evidence retrieval, scaffolding,
provenance stamping, status transitions, mechanical linting, the independent
audit, and continuing an incomplete run (intake goal or plain language — there
is no `--resume` flag).

For each routed document, load `model_depth` from `query_catalog --route` and
apply the minimum rung in [`../references/model-depth-ladders.md`](../references/model-depth-ladders.md).
It is not a heading checklist: verify evidence, decisions, controls, interfaces,
and stopping conditions before requesting independent audit. Document lint also
validates illustration budgets and presentation-safe fences.

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
   markers and provenance tokens, and stamp complete provenance 2.0. The writer
   gathers, verifies, and stamps all candidate `path` / `role` / `git_blob`
   evidence inline:

   - One provenance `sections[]` entry per Markdown heading that makes claims;
     `id` is that heading's anchor.
    - Each claim records at least one repository-relative `path` with `role`
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
   For the `agents-kernel` output (`AGENTS.md`, a `SPECIAL_DOC_OUTPUTS` member
   that `lint_document` skips), the mechanical gate is
   `lint_agents_kernel --file <path> --repo <root>` in place of `lint_document`.
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
do not carry over writer reasoning. For the `agents-kernel` output, its
mechanical gate is `lint_agents_kernel`, not `lint_document`. Record
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
(`lint_document` plus the `scaffold_docs --audit` README child-coverage check),
then the independent audit, and record the result. Never restate child-owned
facts or link a child that is not selected and materialized.

Next: once every selected document passes individually, proceed to
[`validation.md`](validation.md) for the whole-tree gate.
