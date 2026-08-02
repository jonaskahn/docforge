# Common runtime

Shared internal libraries used by the other subsystems. Every module has a
`js/` and a `python/` peer with equivalent APIs. **None of these is a CLI** —
they exist to be imported, not executed.

## Load this when

- You are implementing or modifying a runtime tool → `_util` (JSON, manifests,
  `.docforge` ignore/cleanup).
- Reading or writing provenance frontmatter → `provenance_frontmatter`.
- Planning manifest document actions → `plan`.
- Linting documents → `evidence_locators`, `illustration_metrics`,
  `markdown_fences`.
- Extracting declared dependencies from package manifests → `manifest_deps`.
- Mapping provenance 2.0 to PROV relations → `prov_projection`.
- Naming special outputs that bypass normal provenance → `special_files`.

## Scripts

All are paired libraries (Python snake_case / JS camelCase exports).

| Script | Purpose | Read-only? |
|---|---|---|
| `_util` | JSON/error/manifest helpers, `.docforge/.gitignore` and `tmp/`/`scratch/` cleanup | mixes — mutates `.docforge` state |
| `evidence_locators` | Validate `path#Lx-Ly @ <git-blob>` locators against files and provenance | yes |
| `illustration_metrics` | Enforce Mermaid/ASCII illustration budgets per target depth | yes |
| `manifest_deps` | Extract dependency names + own-package identities from manifests (9 ecosystems) | yes |
| `markdown_fences` | CommonMark fence scanning and visible-presentation policy checks | yes |
| `plan` | Deterministic add/update/rewrite/unchanged/skip plans for documents | yes |
| `prov_projection` | Project provenance 2.0 into ordered PROV relation rows | yes |
| `provenance_frontmatter` | Restricted-YAML provenance codec, v1→v2 migration, hashing, frontmatter rewrite | yes |
| `special_files` | Constants: special output names and their template sources | yes |

## Details

- `_util` — `fail`, `read_json`, `dump_json`, `load_manifest`,
  `ensure_gitignored_dir`, `finish_docforge`. Mutating helpers create/update
  `.docforge/.gitignore` and may delete contents of `tmp/` and `scratch/`.
- `provenance_frontmatter` — `content_hash`, `scaffold_provenance`,
  `migrate_v1_to_v2`, `emit_yaml`, `wrap_document`, `parse_frontmatter`,
  `rewrite_frontmatter`, plus `PROVENANCE_FIELDS` / `SCHEMA_VERSION`. Rejects
  anchors, aliases, block scalars, and multi-document markers.
- `plan` — `flow_is_main_priority`, `document_action`, `plan_entries`,
  `plan_lines`.
- `manifest_deps` — `normalize`, `extract_dependencies(files)`,
  `extract_package_identities(files)`; 1 MiB manifest cap; npm, Composer, pip,
  Cargo, Go, Ruby, Maven/Gradle, NuGet, pub.
- `evidence_locators` — `validate_locators(document, text=None)`; defects for
  path escape, missing source, stale blob, invalid range, unknown heading,
  provenance mismatch.
- `illustration_metrics` — `illustration_defects(text, target_depth)`; budgets
  per depth (e.g. orientation 1 illustration / 5 elements, router 0/0).
- `markdown_fences` — `inferred_role`, `scan_fences`,
  `visible_presentation_defects`.
- `prov_projection` — `project_core(provenance)`; raises on conflicting
  source/blob roles.
- `special_files` — `SPECIAL_DOC_OUTPUTS` (AGENTS.md, CLAUDE.md,
  CLAUDE.local.md) and `SPECIAL_DOC_SOURCES` (agents-kernel.md, claude-md.md,
  claude-local-md.md).

## Where invoked

Library modules — imported by the other subsystems, never executed as
commands. The `cli/` launcher pair mirrors `_util`, `provenance_frontmatter`,
and `manifest_deps` for import compatibility only (no CLI behavior). Known
consumers:

- `documents/` — `_util`, `plan`, `special_files`, `provenance_frontmatter`,
  `evidence_locators`, `illustration_metrics`, `markdown_fences`.
- `manifest/` — `_util`, `plan`, `provenance_frontmatter`.
- `validation/` — `_util`, `provenance_frontmatter`, `special_files`.
- `catalog/` — `manifest_deps` (via `detect_profiles`).
- `portfolio/` — `manifest_deps` (via `discover_child_repos`).
- `dashboard/` — `_util`, `provenance_frontmatter`.
- `graph/` — `_util` (via `graph_storage`).

## Boundaries

Internal only: no public launcher is needed for these modules. Import via the
package-qualified path (`runtime.common.python.<module>` / `../common/js/<module>.js`).
