# Manifest runtime

The persistent Docforge plan/status lifecycle, provenance staleness checking,
and metadata migration. All four scripts are paired Python/JS public
commands with launchers in [`runtime/cli/`](../cli/README.md).

## Load this when

- Starting, extending, or ending a run; changing document status or
  presentation; recording audits → `manage_manifest`.
- Checking whether written documents drifted from their source blobs →
  `check_staleness`.
- Stamping `git_blob_normalized` / `range_blob` while grounding a section →
  `hash_evidence`.
- Loading legacy state (manifest 3.1 / 3.0 / provenance 1.0 or pre-3.0 shapes) →
  `migrate_metadata`.

## Scripts

| Script | js/py | Kind | Purpose |
|---|---|---|---|
| `manage_manifest` | both | CLI | `init` / `preview` / `add` / `set` / `presentation` / `audit` / `status` / `set-graph` / `reconcile` / `retire` / `unmanaged` / `finish` |
| `check_staleness` | both | CLI | Provenance blob drift report (raw / normalized / range-scoped); optional provenance sync |
| `hash_evidence` | both | CLI | Stamp `git_blob` / `git_blob_normalized` / `range_blob` for one cited source |
| `migrate_metadata` | both | CLI | Idempotent manifest 3.9 / provenance 2.1 upgrade + sidecar moves |

## Details

### `manage_manifest`

```sh
python3 runtime/cli/python/manage_manifest.py <subcommand> --repo <repo> ...
```

| Subcommand | Writes | Notes |
|---|---|---|
| `init --tier <tier> [--scale-class <small\|medium\|large>] [--layout <compact\|standard>] [--shape|--platform|--framework|--concern|--audience ...] [--group <id> ...] [--graph-provider <id>]` | `.docforge/manifest.json`, `.gitignore`, `tmp/`, `audits/`, scratch deps | `--force` replaces an existing manifest; auto-locks the graph provider (registry-priority order) unless `--graph-provider` names an explicit choice; scale is auto-detected (source files < 50 → `compact`, dependency / flow breadth promoting one class) unless `--scale-class` / `--layout` record a user override; `--tier portfolio --layout compact` is rejected (compact covers spine and diligence only) and a detected compact layout there is forced to `standard` as `decided_by: "tier-constraint"`; repeatable `--group` restricts the run to those catalog groups and records `project.groups` (out-of-scope indexes are not pulled in as ancestors, so an agents-only run writes no `docs/README.md`); a scope that selects nothing fails rather than writing an empty manifest |
| `preview --tier <tier> [--layout <compact\|standard>] [--shape|--platform|--framework|--concern|--audience ...] [--group <id> ...] [--json]` | **nothing** | read-only scope sizing for intake: static document count in both layouts, plus a per-selection ablation (how many documents disappear if that value is dropped). Reports the constraint instead of a compact count at `--tier portfolio` and reports the projected `groups` scope |
| `add --type --id --path [--title] [--evidence ...]` | manifest (+ `.docforge/flow-index.json` for flows) | validates tier, profiles, path, uniqueness, evidence |
| `set --id --status` | manifest | completion requires a recorded PASS audit |
| `presentation --id ... [--reset]` | manifest | demotes written docs to `in_progress` when output policy changed |
| `audit --id --mode cold-pass --verdict PASS\|FAIL --report <path>` | manifest | requires status `generated`; FAIL → `needs_review` |
| `status` | none | read-only report; includes the locked graph provider when set |
| `set-graph [--provider <id>] [--force]` | manifest | locks/self-heals `manifest["graph"]`; auto-picks the highest-priority ready source when `--provider` is omitted; switching an already-locked provider requires `--force` |
| `reconcile [--tier ...] [--scale-class ...] [--layout ...] [--group <id> ...]` | manifest | re-runs static selection, preserves dynamic/written docs, demotes drift; scale flags record `decided_by: "user"` with fresh measurement signals and the detected class preserved; changing the tier to `portfolio` forces `layout: standard` with `decided_by: "tier-constraint"` |
| `unmanaged --action list\|add\|remove\|archive [--path <rel>] [--dry-run]` | manifest (archive: file move) | self-managed docs the user keeps untracked; `add` records one, `remove` forgets it (file untouched), `archive` moves it into `docs/_archive/<year>/` (or `docs-portfolio/_archive/`) and records the move |
| `retire --doc <id> [--doc <id> ...] --mode obsolete\|delete [--dry-run]` | manifest, `.docforge/obsolete/<year>/` (obsolete mode: file move) | written documents that fell out of selection; entry kept with status `retired`, `retired_at`, and (obsolete mode) `retired_destination` |
| `finish [--keep-tmp]` | `.docforge/.gitignore` | deletes `tmp/` and `scratch/` contents unless kept |

### `check_staleness`

```sh
python3 runtime/cli/python/check_staleness.py --manifest <path> \
  [--document <id-or-path>] [--section <id>] [--json] [--sync-provenance]
```

Default is read-only: reports `FRESH`, `PARTIAL` (`NO_BLOB` / `MISSING` /
`STALE` / `COSMETIC`), `UNTRACKED`, or `UNPARSEABLE`. A `COSMETIC` finding
means the raw blob differs but a source's recorded `git_blob_normalized` or
`range_blob` still matches the current file — whitespace/EOL-only, or the
cited range is untouched — so it does not force re-grounding.
`--sync-provenance` **mutates**: may migrate metadata first, rewrite obsolete
document frontmatter, copy provenance into the manifest, and rewrite the
manifest. Exit `0` when every finding is `FRESH`/`COSMETIC`, `1` when any
`STALE`/`MISSING`/`NO_BLOB`/`UNTRACKED`/`UNPARSEABLE` finding exists, `2` error.

### `hash_evidence`

```sh
python3 runtime/cli/python/hash_evidence.py --repo <repo> --path <repo-relative-path> \
  [--range <start>-<end>] [--json]
```

Prints `git_blob` (matches `git hash-object`) and `git_blob_normalized`
(whitespace/EOL-normalized) for the file; with `--range <start>-<end>`
(1-indexed, inclusive), also prints `evidence_range` and `range_blob` scoped
to just that line span. Read-only. Exit `0` success, `2` error (path escapes
the repo, file missing, or `--range` given against an out-of-bounds or
non-UTF-8 span).

### `migrate_metadata`

```sh
python3 runtime/cli/python/migrate_metadata.py --repo <repo> [--manifest <path>] [--dry-run] [--report]
```

Upgrades manifest 3.8 / 3.7 / 3.6 / 3.5 / 3.4 / 3.3 (or 3.2 / 3.1 / 3.0 / provenance 1.0) to 3.9 / 2.1 —
seeding each document's catalog-owned `description` from the catalog
`summary`, the project's `provenance_storage` (default `json`), the project's
`unmanaged_docs` list (default empty), and the project's `scale` record
(`decided_by: "detected"` from live detection when absent; present records are
never overwritten — their measurement `signals` are refreshed on upgrade with
the 3.7 `declared_dependencies` and `flow_candidates` fields) — and
re-registers older
shapes; adopts legacy written documents, scaffolds incomplete provenance,
clears failed audits, demotes incomplete written documents to `in_progress`.
The same run moves any pre-migration document's inline frontmatter into the
folder sidecars (`.docforge/provenance/<folder>.json`) and strips it from the
markdown. `--dry-run` is read-only; `--report` changes output format
**without** making the run read-only. Exit `1` on missing documents or
failed conversion.

## Where invoked

| Script | Documented callers |
|---|---|
| `manage_manifest` | [`workflows/intake.md`](../../workflows/intake.md), [`workflows/planning.md`](../../workflows/planning.md), [`workflows/writing.md`](../../workflows/writing.md), [`workflows/validation.md`](../../workflows/validation.md), [`workflows/revision.md`](../../workflows/revision.md), [`workflows/tools.md`](../../workflows/tools.md), [`references/document-audit.md`](../../references/document-audit.md), [`references/portfolio.md`](../../references/portfolio.md), plus the `docforge` / `docforge-revise` / `docforge-dashboard` SKILL.md files |
| `check_staleness` | [`workflows/validation.md`](../../workflows/validation.md), [`workflows/revision.md`](../../workflows/revision.md), [`workflows/writing.md`](../../workflows/writing.md), [`workflows/tools.md`](../../workflows/tools.md), [`references/provenance-tracking.md`](../../references/provenance-tracking.md) |
| `hash_evidence` | [`workflows/writing.md`](../../workflows/writing.md), [`references/provenance-tracking.md`](../../references/provenance-tracking.md) |
| `migrate_metadata` | [`workflows/dashboard.md`](../../workflows/dashboard.md), [`workflows/revision.md`](../../workflows/revision.md), [`workflows/validation.md`](../../workflows/validation.md), [`workflows/writing.md`](../../workflows/writing.md), [`workflows/tools.md`](../../workflows/tools.md), [`references/provenance-tracking.md`](../../references/provenance-tracking.md); also invoked programmatically by `check_staleness --sync-provenance`, `scaffold_docs`, `lint_document`, `_util` |

## Boundaries

Consumes `common/` libraries (`_util`, `plan`, `provenance_frontmatter`,
`evidence_hash`) and `catalog/query_catalog`. The manifest schema (3.9) and
flow-index schema (1.1) are enforced by `validation/validate_metadata`.
