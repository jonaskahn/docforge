# Common runtime

Shared internal libraries used by the other subsystems. Every module has a
`js/` and a `python/` peer with equivalent APIs. **None of these is a CLI** —
they exist to be imported, not executed.

## Load this when

- You are implementing or modifying a runtime tool → `_util` (JSON, manifests,
  `.docforge` ignore/cleanup).
- Reading or writing provenance frontmatter → `provenance_frontmatter`.
- Reading or writing a document's provenance sidecar
  (`.docforge/provenance/<folder>.json`), or moving a pre-migration
  document's inline frontmatter into one → `provenance_store`.
- Planning manifest document actions → `plan`.
- Linting documents → `evidence_locators`, `illustration_metrics`,
  `markdown_fences`.
- Checking that a human-facing document does not reference the agent-context
  group → `agent_context`.
- Classifying a source's drift (fresh / cosmetic / stale) → `evidence_hash`.
- Extracting declared dependencies from package manifests → `manifest_deps`.
- Naming special outputs that bypass normal provenance → `special_files`.
- Classifying project scale (`small` / `medium` / `large`) and suggesting a
  layout → `scale`.

## Scripts

All are paired libraries (Python snake_case / JS camelCase exports).

| Script | Purpose | Read-only? |
|---|---|---|
| `_util` | JSON/error/manifest helpers, `.docforge/.gitignore` and `tmp/`/`scratch/` cleanup | mixes — mutates `.docforge` state |
| `agent_context` | Manifest-derived inbound and outbound agent-context isolation checks | yes |
| `evidence_hash` | Raw/normalized/range-scoped blob hashing and fresh/cosmetic/stale classification | yes |
| `evidence_locators` | Validate `path#Lx-Ly @ <git-blob>` locators against files and provenance | yes |
| `illustration_metrics` | Enforce per-illustration Mermaid/ASCII complexity bounds per target depth | yes |
| `manifest_deps` | Extract dependency names + own-package identities from manifests (9 ecosystems) | yes |
| `markdown_fences` | CommonMark fence scanning and visible-presentation policy checks | yes |
| `plan` | Deterministic add/update/rewrite/unchanged/skip plans for documents | yes |
| `provenance_frontmatter` | Restricted-YAML provenance codec: parse, v1→v2 migration, hashing; `emit_yaml` remains only to build pre-migration test fixtures | yes |
| `provenance_store` | Folder-mirrored JSON sidecar store: sidecar-first reads, entry writes, inline-to-sidecar moves | mixes — writes `.docforge/provenance/` and strips migrated frontmatter |
| `special_files` | Constants: special output names and their template sources | yes |
| `scale` | Three-way project scale classification from the existing inventory walk + confirmed profile count; suggests `compact`/`standard` layout | yes |

## Details

- `_util` — `fail`, `read_json`, `dump_json`, `load_manifest`,
  `ensure_gitignored_dir`, `finish_docforge`. Mutating helpers create/update
  `.docforge/.gitignore` and may delete contents of `tmp/` and `scratch/`.
- `provenance_frontmatter` — `content_hash`, `scaffold_provenance`,
  `migrate_v1_to_v2`, `parse_frontmatter`, `parse_yaml_mapping`,
  `split_frontmatter`, plus `PROVENANCE_FIELDS` / `SCHEMA_VERSION`. `emit_yaml`
  remains for constructing pre-migration inline fixtures in tests; nothing in
  the runtime writes frontmatter. Rejects anchors, aliases, block scalars, and
  multi-document markers.
- `provenance_store` — `sidecar_path(repo, folder)`, `entry_for`,
  `write_entry`, `remove_entry`, `read_doc_metadata` (explicit state: `ok` /
  `inline` / `legacy` / `obsolete` / `missing` / `unparseable`),
  `move_inline_to_sidecar`, `public_from_manifest`. Public identity
  (`id`/`title`/`description`) and `docforge_provenance` live in one
  git-tracked JSON per folder under `.docforge/provenance/`; generated
  markdown carries no frontmatter. A document written before the sidecar
  store still carries inline frontmatter until `move_inline_to_sidecar` (via
  `migrate_metadata` or `check_staleness --sync-provenance`) moves it —
  `read_doc_metadata` falls back to reading that layout and reports it as
  `inline`. Old-schema metadata (schema-less legacy or schema 1.0 /
  `tool_version`) is always reported explicitly — never folded into `ok`,
  never silently moved; there is no opt-in/opt-out.
- `plan` — `flow_is_main_priority`, `document_action`, `plan_entries`,
  `plan_lines`.
- `manifest_deps` — `normalize`, `extract_dependencies(files)`,
  `extract_package_identities(files)`; 1 MiB manifest cap; npm, Composer, pip,
  Cargo, Go, Ruby, Maven/Gradle, NuGet, pub.
- `evidence_hash` — `raw_blob_hash`, `git_blob_for_path`, `normalized_blob_hash`,
  `range_blob_hash`, `classify_source(source, current_bytes)` returning
  `missing`/`fresh`/`cosmetic`/`stale`. No git dependency; normalization is
  whitespace/EOL-only (no comment stripping).
- `evidence_locators` — `validate_locators(document, text=None)`; defects for
  path escape, missing source, stale blob, invalid range, unknown heading,
  provenance mismatch.
- `illustration_metrics` — `illustration_defects(text, target_depth)`; bounds
  the elements within a single illustration per depth (orientation 5, all
  others 12). The number of illustrations in a document is never capped.
- `markdown_fences` — `inferred_role`, `scan_fences`,
  `visible_presentation_defects`.
- `special_files` — `SPECIAL_DOC_OUTPUTS` (AGENTS.md, CLAUDE.md,
  CLAUDE.local.md) and `SPECIAL_DOC_SOURCES` (agents-kernel.md, claude-md.md,
  claude-local-md.md).
- `scale` — `compute_scale(repo, files=None, detections=None, dependencies=None)` /
  `computeScale(repo, files, detections, dependencies)` returning
  `{class, suggested_layout, signals}`; thresholds are tunable constants
  (`SMALL_MAX_SOURCE_FILES` = 49, `MEDIUM_MAX_SOURCE_FILES` = 200,
  `DEP_NUDGE_SMALL|MEDIUM`, `FLOW_NUDGE_SMALL|MEDIUM`,
  `BOUNDARY_NUDGE_RATIO`, `PROFILE_NUDGE_THRESHOLD`). Classification:
  source files < 50 → `small` (layout `compact`), 50–200 → `medium`, > 200 →
  `large` (both `standard`). Declared-dependency breadth (`manifest_deps`)
  and flow breadth (`.docforge/flow-index.json` rows, when present) promote
  at most one class above the source-file class; the confirmed-profile count
  still nudges boundary-adjacent repos. `signals` carries `tracked_files`,
  `source_files`, `confirmed_profiles`, `declared_dependencies`, and
  `flow_candidates`. Read-only: reuses `detect_profiles.inventory` and
  non-persisting detection. Pass `files`, `detections`, and `dependencies`
  when the caller already walked the repository — `init` does, so one walk
  serves both the discovery record and the scale record.

## Where invoked

Library modules — imported by the other subsystems, never executed as
commands. The `cli/` launcher pair mirrors `_util`, `provenance_frontmatter`,
and `manifest_deps` for import compatibility only (no CLI behavior). Known
consumers:

- `documents/` — `_util`, `plan`, `special_files`, `provenance_frontmatter`,
  `provenance_store`, `evidence_locators`, `illustration_metrics`,
  `markdown_fences`, `agent_context`.
- `manifest/` — `_util`, `plan`, `provenance_frontmatter`, `provenance_store`,
  `evidence_hash`.
- `validation/` — `_util`, `provenance_frontmatter`, `special_files`.
- `catalog/` — `manifest_deps` (via `detect_profiles`), `scale` (via
  `detect_profiles --emit-gate-pack`, lazily to avoid the import cycle).
- `portfolio/` — `manifest_deps` (via `discover_child_repos`).
- `dashboard/` — `_util`, `provenance_frontmatter`, `provenance_store`,
  `evidence_hash`.
- `flows/` — `_util`, `provenance_frontmatter`, `provenance_store`.
- `graph/` — `_util` (via `graph_storage`).

## Boundaries

Internal only: no public launcher is needed for these modules. Import via the
package-qualified path (`runtime.common.python.<module>` / `../common/js/<module>.js`).
