# Runtime

Implementations behind every public CLI launcher under
[`cli/`](cli/README.md). Business logic lives in the subsystem folders below;
every subsystem is split into a `js/` and a `python/` peer folder, and
`cli/python/` / `cli/js/` hold only thin re-exports.

## Load this when

- Modifying a command's behavior → edit the matching subsystem
  implementation (never the launcher).
- Adding a new public command → implement it in both `python/` and `js/`
  under the matching subsystem, then add a launcher pair in `cli/python/`
  and `cli/js/`.

## Contents

Each subsystem folder carries a `js/` and a `python/` directory:

- [`cli/`](cli/README.md) — public launchers, split by language.
- `common/` — shared helpers: `_util`, `manifest_deps`,
  `provenance_frontmatter`.
- `catalog/` — catalog query and profile detection: `query_catalog`,
  `detect_profiles`, `discovery_gate`.
- [`graph/`](graph/README.md) — graph-provider adapters, storage, and
  precondition checks.
- `flows/` — flow-index harvesting and provisional derivation: `flow_index`,
  `derive_flow_graph`.
- `manifest/` — manifest lifecycle and migration: `manage_manifest`,
  `migrate_metadata`, `check_staleness`.
- `documents/` — scaffolding and linting: `scaffold_docs`, `lint_document`,
  `lint_agents_kernel`.
- `dashboard/` — local Fumadocs site build and serve: `dashboard` (see
  [`dashboard/README.md`](dashboard/README.md)).
- `portfolio/` — cross-repository discovery: `discover_child_repos`.
- `validation/` — registry and router validation: `validate_metadata`,
  `generate_indexes`.
- `migrations/` — one-shot, Python-only metadata migration tools:
  `split_catalog`, `split_document_catalog`.

## Boundaries

Every subsystem module is imported by its `cli/` launcher via a
package-qualified path (`runtime.<subsystem>.python.<module>`) or a relative
`require()` (`../<subsystem>/js/<module>.js`) — never the reverse. No
subsystem module imports from `cli/`.
