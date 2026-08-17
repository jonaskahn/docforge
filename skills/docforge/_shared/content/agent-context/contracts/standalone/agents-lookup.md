# `agents-flow` — standalone

Standalone content contract for document type `agents-flow`.

Aliased with: `agents-glossary` (same content contract).

In force when `project.agent_context.mode` is `standalone`: this repository has
no `docs/flows/` or `reference/glossary.md` to route to, so this view is the
only flow or vocabulary lookup it has. It states each entry itself, still
bounded by the declared flow evidence — standalone never licenses an inferred
flow or an invented definition.

| Type | Must present | Keep out | Primary mode | Depth |
|---|---|---|---|---|
| agents-flow | compact flow/term lookup that owns its entries, grounded in declared flow evidence: trigger, entry point, durable module hops, terminal effect, or a short evidence-backed definition with the module that owns the term | inferred flows, invented definitions, duplicated business prose, links to human-facing documents this run did not generate | Reference | reference |
