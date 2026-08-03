# Flow index (`flow-index`) writing craft

Every candidate row includes an evidence locator, confidence basis, and explicit
priority; sort by that evidenced priority, never by assumed reach. Retain
unresolved candidates as `placeholder` or `skipped`, not inferred flows.

This is the router for the whole flow layer, not a flow itself: a reader
scans it to decide which flow to open, or whether a candidate they expected
even surfaced. Group rows by family (or "Ungrouped") and sort by priority
within a group, main before deferred. State the status vocabulary once at the
top: `main` / `deferred` / `placeholder` / `documented` / `skipped`.

Every row must trace to an evidenced candidate; never add a row for a
heuristic guess or an invented execution order. `standalone` rows get their
own deep-dive document; `member` rows are folded into a parent under
`composed_into`; `index_only` rows stay discoverable without a stub file.
Keep the row itself terse — trigger kind, normalized entry signature, area,
confidence, reach — and never restate the flow's steps, branches, or failures
here; those belong solely to the `flow` document once it exists.

## Illustration

- **Form:** Markdown table only.
- **Renders:** nothing beyond the table; do not add a relationship diagram
  even for a large flow set.
- **Trigger:** never — orientation depth caps this document at prose plus
  the table itself, per [`illustration.md`](../../references/illustration.md).

## Connections

| This document owns | Links to | Because |
|---|---|---|
| Discovery status, role, area, confidence, reach for every candidate | each `standalone`/`main` row's `flow` document | the index routes; the flow document owns the actual steps |
| — | `.docforge/flow-index.json` (declared as the machine-readable source of truth) | this document is the human-readable projection of that file, never a second source of truth |
| A `member` row's `composed_into` id | the parent flow document's matching H2 section | keeps composed members traceable without duplicating their content here |
