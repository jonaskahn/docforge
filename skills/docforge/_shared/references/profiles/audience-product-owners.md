# Product Owner audience profile

Select the `product-owners` audience when readers need value, delivery state, measurable
outcomes, and release impact. Product value is not inferable from architecture
alone; code and history establish shipped behavior, while stakeholder evidence
owns intent and targets.

## Generated structure

```text
docs/product/product-owner/
├── README.md
├── feature-catalog.md
├── success-metrics.md
├── release-notes.md
└── backlog-traceability.md   # dynamic; ticket evidence only
```

The first four entries are static for the profile. `backlog-traceability.md`
enters the manifest only after discovery proves that ticket evidence exists.
It is never scaffolded and later deleted as cleanup.

## Content ownership

### `README.md`

Route product readers to value/status, metrics, and release impact. Link to the
BA view only when that profile is selected.

### `feature-catalog.md`

For every evidenced user-facing feature, record:

- user or business outcome;
- audience;
- availability/status and the evidence for that state;
- owning capability and flow links;
- material dependencies or constraints.

Link to `docs/product/overview.md` for the general capability description.
This file contributes value and delivery framing rather than restating it.
“Shipped” requires a reachable code path and release/deployment evidence, not
merely code present in the tree.

### `success-metrics.md`

Record the desired outcome, measurable signal, instrumentation source,
interpretation, and ownership. A code-emitted event or metric proves
instrumentation, not the business target. Include a target only when
stakeholder or connected planning evidence supplies it; otherwise use the
appropriate typed external token or state that no target is documented.

### `release-notes.md`

Translate released changes into user impact by correlating release tags,
merge/history evidence, and the feature catalog. Exclude refactors, test-only
changes, and dependency noise unless they materially change user behavior,
compatibility, security, or operations.

### `backlog-traceability.md`

When ticket IDs or a connected tracker provide evidence, map ticket → feature
→ flow/change → verification/release. Add it with `manage_manifest add` using
the dynamic `backlog-traceability` type. If evidence is absent, the correct
result is no manifest entry and no file.

## Evidence recipe

Follow the evidence loop in [`source-analysis.md`](../source-analysis.md):

1. Use the code graph to discover externally reachable capabilities and their owning paths.
2. Use manifests and configuration for availability and instrumentation.
3. Use git history/tags for delivery chronology and release impact.
4. Use flow evidence only for links when it exists (PO does not globally require `flow_graph`).
5. Treat stakeholder intent, target values, owners, dates, and roadmap state as external evidence.
