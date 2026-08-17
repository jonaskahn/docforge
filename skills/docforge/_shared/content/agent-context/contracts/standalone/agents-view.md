# `agents-architecture` — standalone

Standalone content contract for document type `agents-architecture`.

Aliased with: `agents-patterns`, `agents-testing`, `agents-tech-debt`, `agents-conventions` (same content contract).

In force when `project.agent_context.mode` is `standalone`: no human-facing
document exists to own these facts, so this view owns them. Owning a fact the
linked-mode contract lists under Keep out is correct here and is not an audit
failure. Linking a human-facing document that was never generated **is** —
it is both a dead link and a fact with no owner.

| Type | Must present | Keep out | Primary mode | Depth |
|---|---|---|---|---|
| agents-architecture | token-budgeted retrieval view that owns its facts: durable paths, boundaries, entry points, constraints, verified commands, observable hazards | design rationale, business context, operational procedure, roadmap, narrative history, volatile symbol dumps, links to human-facing documents this run did not generate | Reference | deep-dive |
