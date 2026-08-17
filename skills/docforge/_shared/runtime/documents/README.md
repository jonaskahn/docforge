# Documents runtime

Mechanical document linting and scaffolding. Every script is a paired
Python/JS public command with a launcher in
[`runtime/cli/`](../cli/README.md).

## Load this when

- One document needs a mechanical pre-audit → `lint_document`.
- The document is an `agents-kernel` special output (AGENTS.md or CLAUDE.md) → `lint_agents_kernel`.
- Previewing the exact manifest tree, materializing one document, or auditing
  the whole tree → `scaffold_docs`.

## Scripts

| Script | js/py | Kind | Purpose |
|---|---|---|---|
| `lint_document` | both | CLI | Mechanical lint of one ordinary Docforge document |
| `lint_agents_kernel` | both | CLI | Rubric lint of an AGENTS/CLAUDE agent-kernel document |
| `scaffold_docs` | both | CLI | Dry-run plan, single-document materialization, or tree audit |

## Details

### `lint_document`

```sh
python3 runtime/cli/python/lint_document.py --file <path> [--require-heading <text> ...] [--json]
```

Checks provenance, source blobs, evidence locators, illustration budgets,
Markdown presentation, scaffold markers, headings, links, unlinked mentions,
and forge leakage. Read-only. Exit `0` clean, `1` defects, `2` usage error.
Typed `<UPPER_SNAKE>` tokens are reported but are not defects. This is a
mechanical pre-audit, never a substitute for the independent semantic audit.

### `lint_agents_kernel`

```sh
python3 runtime/cli/python/lint_agents_kernel.py --file <path> [--json]
```

Rubric for an AGENTS/CLAUDE kernel: 80-nonblank-line cap, required operating
sections and order, a concrete command block, mandatory safety rules, one code
block, provenance comment, and no document references. `--repo` remains
accepted for compatibility but is not needed. Read-only. Exit `0` no defects,
`1` defects, `2` usage error.

### `scaffold_docs`

Materializes templates per `project.provenance_storage`: `json` (default)
writes clean markdown plus a `.docforge/provenance/<folder>.json` sidecar
entry; `markdown` emits inline frontmatter.

```sh
python3 runtime/cli/python/scaffold_docs.py --repo <repo> --manifest <manifest> \
  (--dry-run [--revise] | --document <id> | --audit)
```

- `--dry-run` — read-only; prints the exact manifest-backed plan.
- `--document <id>` — **writes**: ensures `.docforge/.gitignore`, creates
  ancestor indexes and the target scaffold, deep-merges machine config, adds
  `CLAUDE.local.md` to the repository `.gitignore`. Existing non-machine
  documents are never overwritten.
- `--audit` — read-only; reports missing/unexpected files, placeholders,
  provenance defects, links, README child coverage, invalid JSON, folder-only
  indexes, forge leakage, and both directions of the generated agent-context
  isolation boundary.

## Where invoked

| Script | Documented callers |
|---|---|
| `lint_document` | [`workflows/writing.md`](../../workflows/writing.md), [`workflows/revision.md`](../../workflows/revision.md), [`references/document-audit.md`](../../references/document-audit.md) |
| `lint_agents_kernel` | [`workflows/writing.md`](../../workflows/writing.md), [`references/document-audit.md`](../../references/document-audit.md), [`references/profiles/audience-coding-agents.md`](../../references/profiles/audience-coding-agents.md) |
| `scaffold_docs` | [`workflows/planning.md`](../../workflows/planning.md), [`workflows/writing.md`](../../workflows/writing.md), [`workflows/validation.md`](../../workflows/validation.md), [`content/shared/topic-readme.template.md`](../../content/shared/topic-readme.template.md) |

## Boundaries

Consumes `common/` libraries (plan, provenance, special files, locators,
metrics, fences). Owns no manifest mutation; the launchers are thin re-exports
of these implementations.
