# Tools

Owns: every public script, its Python and Node invocation forms, inputs,
outputs, side effects, and exit-code expectations.

Every script has standard-library Python and built-in-only Node peers with the
same flags, messages, JSON shapes, filesystem effects, and exit codes. Unknown
flags exit `2`. Use Node by replacing `python scripts/name.py` with
`node scripts/name.js`.

- `query_catalog.{py,js}`: read the catalog (`--tier`, `--id`, `--ids`,
  `--profile`, `--applicable`, `--validate`, `--category <group>`,
  `--route <id>`). Every workflow step uses this instead of opening catalog
  files directly.
- `generate_indexes.{py,js}`: regenerate catalog routers (`--write`,
  `--check`). `--check` exits `1` without writing when generated output is
  stale.
- `manage_manifest.{py,js}`: `init`, `add`, `set`, `status`, and `audit`.
- `detect_profiles.{py,js}`: read-only shape/platform/framework/concern
  recommendations with strong/weak match strength, cue bags, and
  `confirmed|candidate` confidence; `--emit-gate-pack` for agent intake.
- `discovery_gate.{py,js}`: validate/apply discovery-gate judgment JSON
  (offline; fail-open).
- `scaffold_docs.{py,js}`: exact dry-run, one-document materialization, and
  manifest-backed audit.
- `precheck_graph.{py,js}`: `--need code|flow`.
- `check_staleness.{py,js}`: `--section`, JSON output, and provenance sync.
- `migrate_metadata.{py,js}`: dry-run, report, and idempotent metadata upgrade;
  incomplete or unconvertible written documents are reported as `FAILED` and
  demoted to `in_progress` for agent regeneration.
- `flow_index.{py,js}`: harvest, revise (label/candidate dedup, compact
  communities summary, placeholder stubs, main NOTICE), and render the flow
  matrix; GitNexus input uses deterministic MCP-export JSON.
- `validate_metadata.{py,js}`: registry/schema/path/version/peer validation,
  including generated-router drift (`generate_indexes --check`).
- Graph adapters, readers, derivation, document lint, and child-repository
  discovery retain paired contracts.

## Canonical example

```sh
python scripts/query_catalog.py --route <document-id>
```

Returns the document's group, summary, definition path, contract,
instruction (or `null`), template, owning workflow, and required
capabilities in one call — see the retrieval protocol in `../SKILL.md`.
