# Business Analyst audience profile

Select the `business-analysts` audience when readers need the system translated into
business processes, enforceable rules, and requirement-to-verification links.
This is an audience view over repository evidence, not a second architecture
tree.

## Generated structure

```text
docs/product/business-analyst/
├── README.md
├── process-flows.md
├── business-rules.md
└── requirements-traceability.md
```

The dry-run plan must show all four paths and identify the three substantive
documents as `flow_graph` consumers. The profile does not make unrelated spine
or agent documents depend on a flow graph.

## Content ownership

### `README.md`

Route a BA to the process, rule, and traceability view. Link to the Product
Owner view only when that profile is selected.

### `process-flows.md`

Present each discovered flow in language a domain expert recognizes:

- actor and trigger;
- ordered business steps;
- decision points and exceptions;
- successful and unsuccessful outcomes;
- link to the canonical dynamic document under `docs/flows/`.

The canonical dynamic flow owns technical sequence and detailed failure paths.
This BA view owns the business-language summary and must not paste raw call
chains.

### `business-rules.md`

Record one stable rule per block: identifier, plain-language statement,
trigger, outcome, exceptions, owning process, enforcement evidence, and test
evidence. A branch name is a lead, not proof. Confirm the condition and its
effect against source.

### `requirements-traceability.md`

Map only evidenced requirements to owning rules/flows, implementation areas,
verification, and current status. Preserve stakeholder wording when available.
Use one typed external token for a missing external requirement identifier or
wording; never invent a ticket.

## Evidence recipe

Follow the evidence loop in [`source-analysis.md`](../source-analysis.md):

1. Query native provider flows first (Understand Anything domain flows or
   GitNexus Process nodes); if unavailable, use Docforge’s provisional derivation from the selected code graph.
2. Confirm actors, branches, rules, exceptions, and outcomes in narrow source paths returned by the graph.
3. Inspect tests for executable verification.
4. Use existing requirements/tickets only when present in source or connected by the user.
5. Add provenance per section; if flow evidence is not ready, these three documents wait at `planned`.
