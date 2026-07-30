# Runtime

Python and Node implementations behind every `scripts/*.py`/`*.js` launcher.
Business logic lives here; `scripts/` holds only thin re-export launchers —
see [`../scripts/README.md`](../scripts/README.md).

## Load this when

- Modifying a script's actual behavior → find its subsystem below, edit the
  implementation there (never the launcher).
- Adding a new public command → implement it in the matching subsystem in
  both Python and Node, then add a launcher pair in `scripts/`.

## Contents

- `common/` — shared helpers with no CLI: `_util`, `manifest_deps`,
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
- `portfolio/` — cross-repository discovery: `discover_child_repos`.
- `validation/` — registry and router validation: `validate_metadata`,
  `generate_indexes`.
- `migrations/` — one-shot, Python-only metadata migration tools:
  `split_catalog`, `split_document_catalog`.

## Boundaries

Every subsystem module is imported by its `scripts/` launcher via a
package-qualified path (Python) or a relative `require()` (Node) — never the
reverse. No runtime module imports from `scripts/`.
