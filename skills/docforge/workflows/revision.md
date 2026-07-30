# Revision

Owns: `--resume`, `--status`, `--revise all`, `--revise <area>`,
`--revise flow`, flow-index organization, and provisional flow derivation.

- `--resume`: run `migrate_metadata` when needed, load the version-3.1
  manifest, and continue the first non-complete, non-skipped document in write
  order. Proceed to [`writing.md`](writing.md) for that document.
- `--status`: print manifest state only.
- `--revise all` / `--revise <area>`: run `migrate_metadata` when needed, check
  provenance, re-ground stale sections in scope, and preserve fresh sections.

## `--revise flow`

Natural-language **revise flow** follows the same procedure:

1. Run `migrate_metadata` when needed, then precheck `--need flow`.
2. Run `flow_index revise` to re-harvest candidates (with community-label and
   near-candidate dedup), upsert every row into `.docforge/flow-index.json`
   (schema 1.1), set non-documented/non-skipped rows to `placeholder`, create
   stub markdown **only for main-priority standalone** placeholders, prune
   orphan deferred / member / index-only scaffolds, and emit compact
   `.docforge/tmp/communities.md` when a GitNexus export is present.
3. Run `flow_index organize emit`, have the agent write
   `.docforge/tmp/flow-organization.json` (descriptive names, families,
   composition), and `flow_index organize apply` before deep-dive analysis.
4. Build an analysis pack from main-priority **standalone** flow-index rows,
   the compact communities summary, and (when no native flow graph)
   `derive_flow_graph prepare` context; the agent/LLM analyzes those
   standalone mains only into `.docforge/tmp/flow-analysis.json`, then runs
   `derive_flow_graph write` when a provisional graph is required. Full
   derivation reasoning:
   [`../references/graph/flow-derivation.md`](../references/graph/flow-derivation.md).
5. Re-ground existing documented flow docs and fully write main standalone
   flows (via [`writing.md`](writing.md)). Always display a NOTICE listing
   main-priority flows being generated; pause for confirmation in review
   mode, or display and continue under `--auto-accept`.
6. Render `docs/flows/README.md`.

Distinct from `--revise <area>`, which re-grounds prose sections without
re-harvesting the flow index.

An explicit single-document request still requires graph precheck,
re-grounding, mechanical lint, independent audit, and manifest state updates
regardless of which invocation mode reached it.
