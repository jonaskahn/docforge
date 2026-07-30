# Graph

Code-graph and flow-graph provider selection, per-provider read mechanisms,
flow derivation, and how to add a new provider.

## Load this when

- Choosing or dispatching to a ready provider → [graph-sources.md](graph-sources.md)
- Reading CodeGraph's SQLite index → [graph-source-codegraph.md](graph-source-codegraph.md)
- Reading GitNexus's LadybugDB graph and processes → [graph-source-gitnexus.md](graph-source-gitnexus.md)
- Reading Understand Anything's JSON graphs → [graph-source-understand-anything.md](graph-source-understand-anything.md)
- Harvesting, revising, or organizing the flow index → [flow-derivation.md](flow-derivation.md)
- Integrating a fourth graph provider → [adding-a-graph-source.md](adding-a-graph-source.md)

## Contents

- [graph-sources.md](graph-sources.md) — dispatch, provider selection, native query mechanisms.
- [graph-source-codegraph.md](graph-source-codegraph.md) — CodeGraph provider detail.
- [graph-source-gitnexus.md](graph-source-gitnexus.md) — GitNexus provider detail.
- [graph-source-understand-anything.md](graph-source-understand-anything.md) — Understand Anything provider detail.
- [flow-derivation.md](flow-derivation.md) — flow-index harvest/revise/organize and provisional derivation.
- [adding-a-graph-source.md](adding-a-graph-source.md) — the three touch points for a new provider.

## Boundaries

Owns everything provider-specific: setup, detection, native flow capability,
and the derivation fallback. Does not own selection *policy* (provider
sufficiency, when to ask the user) — that stays in `workflows/intake.md`.
