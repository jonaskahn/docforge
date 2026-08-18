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

Each subsystem folder carries a `js/` and a `python/` directory and a README
that lists every script, its purpose, and when to use it:

- [`cli/`](cli/README.md) — public launchers, split by language (invoke tools
  here, never the implementations directly).
- [`common/`](common/README.md) — shared libraries: `_util`, `manifest_deps`,
  `provenance_frontmatter`, `plan`, `special_files`,
  `illustration_metrics`, `markdown_fences`, `agent_context`.
- [`catalog/`](catalog/README.md) — catalog query and profile detection:
  `query_catalog`, `detect_profiles`, `discovery_gate`.
- [`graph/`](graph/README.md) — graph-provider adapters, storage, and
  precondition checks.
- [`flows/`](flows/README.md) — flow-index harvesting and provisional
  derivation: `flow_index`, `derive_flow_graph`.
- [`manifest/`](manifest/README.md) — manifest lifecycle and migration:
  `manage_manifest`, `migrate_metadata`, `check_staleness`.
- [`documents/`](documents/README.md) — scaffolding and linting:
  `scaffold_docs`, `lint_document`, `lint_agents_kernel`.
- [`dashboard/`](dashboard/README.md) — local Fumadocs site build and serve:
  `dashboard`.
- [`portfolio/`](portfolio/README.md) — cross-repository discovery:
  `discover_child_repos`.
- [`validation/`](validation/README.md) — registry and router validation:
  `validate_metadata`, `generate_indexes`.
- [`migrations/`](migrations/README.md) — one-shot, Python-only metadata
  migration tools: `split_catalog`, `split_document_catalog`.

## Boundaries

Every subsystem module is imported by its `cli/` launcher via a
package-qualified path (`runtime.<subsystem>.python.<module>`) or a relative
`require()` (`../../<subsystem>/js/<module>.js`) — never the reverse. No
subsystem module imports from `cli/`.

Most tools come as equivalent Python and JS peers; a few subsystems are
library-only (`common/`, and `catalog/discovery_gate`) and `migrations/` is
Python-only. Per-script side effects (read-only vs. writing) are stated in
each subsystem README.
