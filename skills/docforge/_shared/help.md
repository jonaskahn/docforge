# Docforge command help

Canonical `--help` reference for the three Docforge entrypoints. Slash
commands and skills route `--help` here instead of running a workflow: show
the matching section verbatim and stop.

## `/docforge`

Purpose: fresh-start documentation mode — plan and write new documentation
from repository evidence, driven by the Docforge catalog, with bounded
repository-evidence retrieval, manifest metadata, independent audits, and
equivalent Python/Node tools.

| Parameter | Meaning |
|---|---|
| *(none)* | Interactive intake → plan → write, then validate and (unless skipped) auto-serve the dashboard |
| `--plan-only` | Analyze and show the plan / dry-run tree; do not write or re-ground document bodies |
| `--auto-accept` | Display plans/trees/results, then continue without routine conversational pauses (never waives side-effect gates: provider install, graph build, manifest init, file archive/delete) |
| `--no-dashboard` | Skip the automatic dashboard build/serve at run completion; render later with `/docforge-dashboard` |
| `--help` | Show this reference and stop |

Example: `/docforge --plan-only`.

Natural-language update / refresh of a named document uses the same command
(staleness-first revision, not a full rewrite).

## `/docforge-revise`

Purpose: structural refresh of the repository documentation — revise all, a
docs area, or the flow index, with the same catalog, manifest, provenance,
and audit discipline as `/docforge`. A bare invocation migrates manifest
metadata only (no scope question, no writing).

| Parameter | Meaning |
|---|---|
| *(none)* | Metadata-only: migrate/upgrade the manifest metadata via `migrate_metadata.{py,js}` (dry-run preview first, apply only when needed); no scope question, no detection, no writing, no dashboard |
| `flow` | Full flow pipeline (harvest, rank, organization, provisional derivation) |
| `<area>` | Scoped revise of one docs area (architecture, flows, operations, …) |
| `all` | Full-tree revise |
| `--plan-only` | Revise analysis only (migrate, staleness, detect/catalog, dry-run tree); no body writes |
| `--auto-accept` | Same as `/docforge` — display, then continue without routine pauses; side-effect gates stay |
| `--no-dashboard` | Skip the automatic dashboard build/serve at run completion |
| `--help` | Show this reference and stop |

Example: `/docforge-revise flow --plan-only`.

## `/docforge-dashboard`

Purpose: render the written Docforge documentation as a local Fumadocs site
under `<repo>/.docforge/dashboard/` — a generated, git-ignored, disposable
directory that never touches the repository's package files. A **view**, not
a documentation source; the source of truth stays `docs/` Markdown and
`.docforge/manifest.json`.

| Parameter | Meaning |
|---|---|
| *(none)* | Scan diagnostics → `dashboard start`: reconcile metadata → rebuild generated output when the working-tree signature changed → serve → open |
| `--force` | Ignore signatures: always regenerate generated output, keeping `node_modules` |
| `--plan-only` | Preflight, metadata dry-run, signatures, and route plan; no conversion, no writes, no server |
| `--auto-accept` | Skip the revise-vs-render prompt and routine pauses; never authorizes npm install of new packages without its own confirmation gate |
| `--help` | Show this reference and stop |

Subcommands: `scan` (read-only diagnostics: missing metadata, incomplete or
missing documents, stale provenance sources, broken links, route-plan
problems, untracked `docs/` files — each tagged blocking or advisory; exits 1
when anything is found — "you should revise again"), `start` (build-if-changed
→ serve → open, stopping before build on any blocking finding), `export`
(build-if-changed → static HTML export: `next build` emits `index.html` per
page under `<dashboard>/out/` for static hosting (GitHub Pages, S3, …) at a
domain root; no server, no browser; takes no flags), `status` (read-only
state), `stop` (shut down the detached dev server).

A legacy manifest (any pre-3.0 version — 1.1 `project_context` /
`document_groups`, 2.0 flat `documents` with overlays, or another shape) is
auto-migrated to 3.3 by `start`/`export` (never a stop-and-ask gate:
`migrate_metadata` is safe, idempotent, re-registers any legacy version, and
never touches document bodies — the migration is always printed).
`--plan-only` runs the `migrate_metadata --dry-run` preview instead of
migrating; `scan`/`status` stay strictly read-only and never migrate. See
`workflows/dashboard.md`.
