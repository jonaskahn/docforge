# Manifest runtime

The persistent Docforge plan/status lifecycle, provenance staleness checking,
and metadata migration. All three scripts are paired Python/JS public
commands with launchers in [`runtime/cli/`](../cli/README.md).

## Load this when

- Starting, extending, or ending a run; changing document status or
  presentation; recording audits → `manage_manifest`.
- Checking whether written documents drifted from their source blobs →
  `check_staleness`.
- Loading legacy state (manifest 3.0 / provenance 1.0 or pre-3.0 shapes) →
  `migrate_metadata`.

## Scripts

| Script | js/py | Kind | Purpose |
|---|---|---|---|
| `manage_manifest` | both | CLI | `init` / `add` / `set` / `presentation` / `audit` / `status` / `reconcile` / `finish` |
| `check_staleness` | both | CLI | Provenance blob drift report; optional provenance sync |
| `migrate_metadata` | both | CLI | Idempotent manifest 3.1 / provenance 2.0 upgrade |

## Details

### `manage_manifest`

```sh
python3 runtime/cli/python/manage_manifest.py <subcommand> --repo <repo> ...
```

| Subcommand | Writes | Notes |
|---|---|---|
| `init --tier <tier> [--shape|--platform|--framework|--concern|--audience ...]` | `.docforge/manifest.json`, `.gitignore`, `tmp/`, `audits/`, scratch deps | `--force` replaces an existing manifest |
| `add --type --id --path [--title] [--evidence ...]` | manifest (+ `.docforge/flow-index.json` for flows) | validates tier, profiles, path, uniqueness, evidence |
| `set --id --status` | manifest | completion requires a recorded PASS audit |
| `presentation --id ... [--reset]` | manifest | demotes written docs to `in_progress` when output policy changed |
| `audit --id --mode cold-pass --verdict PASS\|FAIL --report <path>` | manifest | requires status `generated`; FAIL → `needs_review` |
| `status` | none | read-only report |
| `reconcile [--tier ...]` | manifest | re-runs static selection, preserves dynamic/written docs, demotes drift |
| `finish [--keep-tmp]` | `.docforge/.gitignore` | deletes `tmp/` and `scratch/` contents unless kept |

### `check_staleness`

```sh
python3 runtime/cli/python/check_staleness.py --manifest <path> \
  [--document <id-or-path>] [--section <id>] [--json] [--sync-provenance]
```

Default is read-only: reports `FRESH`, `PARTIAL` (`NO_BLOB` / `MISSING` /
`STALE`), `UNTRACKED`, or `UNPARSEABLE`. `--sync-provenance` **mutates**: may
migrate metadata first, rewrite obsolete document frontmatter, copy provenance
into the manifest, and rewrite the manifest. Exit `0` clean, `1` stale/untracked,
`2` error.

### `migrate_metadata`

```sh
python3 runtime/cli/python/migrate_metadata.py --repo <repo> [--manifest <path>] [--dry-run] [--report]
```

Upgrades manifest 3.0 / provenance 1.0 to 3.1 / 2.0 and re-registers older
shapes; adopts legacy written documents, scaffolds incomplete provenance,
clears failed audits, demotes incomplete written documents to `in_progress`.
`--dry-run` is read-only; `--report` changes output format **without** making
the run read-only. Exit `1` on missing documents or failed conversion.

## Where invoked

| Script | Documented callers |
|---|---|
| `manage_manifest` | [`workflows/intake.md`](../../workflows/intake.md), [`workflows/planning.md`](../../workflows/planning.md), [`workflows/writing.md`](../../workflows/writing.md), [`workflows/validation.md`](../../workflows/validation.md), [`workflows/revision.md`](../../workflows/revision.md), [`workflows/tools.md`](../../workflows/tools.md), [`references/document-audit.md`](../../references/document-audit.md), [`references/portfolio.md`](../../references/portfolio.md), plus the `docforge` / `docforge-revise` / `docforge-dashboard` SKILL.md files |
| `check_staleness` | [`workflows/validation.md`](../../workflows/validation.md), [`workflows/revision.md`](../../workflows/revision.md), [`workflows/writing.md`](../../workflows/writing.md), [`workflows/tools.md`](../../workflows/tools.md), [`references/provenance-tracking.md`](../../references/provenance-tracking.md) |
| `migrate_metadata` | [`workflows/dashboard.md`](../../workflows/dashboard.md), [`workflows/revision.md`](../../workflows/revision.md), [`workflows/validation.md`](../../workflows/validation.md), [`workflows/writing.md`](../../workflows/writing.md), [`workflows/tools.md`](../../workflows/tools.md), [`references/provenance-tracking.md`](../../references/provenance-tracking.md); also invoked programmatically by `check_staleness --sync-provenance`, `scaffold_docs`, `lint_document`, `_util` |

## Boundaries

Consumes `common/` libraries (`_util`, `plan`, `provenance_frontmatter`) and
`catalog/query_catalog`. The manifest schema (3.1) and flow-index schema (1.1)
are enforced by `validation/validate_metadata`.
