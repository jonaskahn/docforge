# Document catalog

This file owns content contracts: must-present material, keep-out boundaries,
primary mode, and target depth. Selection, paths, evidence capabilities, write
order, templates, and audit profiles are machine-readable in
`.metadata/catalog.json`.

## Universal contract

Every substantive document must:

- answer the reader question implied by its type;
- cite the repository evidence used by each section;
- describe current behavior, boundaries, failure modes, and adjacent systems;
- keep rationale in decision records and volatile lookup facts in reference
  documents;
- link to facts owned elsewhere instead of repeating them;
- contain no unresolved scaffold markers.

Router/index documents orient and link. Procedure documents are executable in
order. Reference documents optimize lookup. Explanation documents establish
mechanism, constraints, and tradeoffs.

## Core types

| Type | Must present | Keep out | Primary mode | Depth |
|---|---|---|---|---|
| root-readme | purpose, audience, verified quick start, links to setup/architecture/limitations | deep architecture and duplicated setup | Orientation | orientation |
| docs-index / folder-index | selected children and one-line purpose | unselected or future links | Orientation | orientation |
| product-overview | users, problems, capabilities, explicit non-goals | invented roadmap or implementation detail | Explanation | orientation |
| architecture-high-level | context, deployable blocks, boundaries, communication, invariants | decision rationale and code listings | Explanation | deep-dive |
| architecture-low-level | subsystem responsibilities, data/control paths, failure boundaries | duplicated high-level map | Explanation | deep-dive |
| setup-guide | prerequisites, install, configuration, run, verification, recovery | unverified commands | How-to | deep-dive |
| testing-guide | test layers, commands, fixtures, isolation, failure diagnosis | generic testing advice | How-to | deep-dive |
| configuration | every read setting, default, scope, sensitivity, validation | secrets or aspirational settings | Reference | reference |
| limitations-register | known bounds, trigger, impact, workaround, source evidence | hidden issues or roadmap promises | Reference | deep-dive |
| dependencies-inventory | direct dependencies/integrations, purpose, criticality, failure behavior | generated lockfile dump | Reference | deep-dive |
| constraints | hard bounds and non-goals | temporary shortcuts | Explanation | deep-dive |
| tech-debt-register | shortcut, consequence, evidence, remediation direction | hard constraints | Reference | deep-dive |
| security-policy | supported scope, reporting path, response expectations, safe harbor | threat-model detail | Reference | router |
| threat-model | assets, trust boundaries, threats, controls, residual risk | disclosure workflow | Explanation | deep-dive |
| data-handling | data classes, lifecycle, access, retention, deletion | invented compliance claims | Reference | deep-dive |
| deployment | environments, artifact path, rollout, rollback, verification | incident procedures | How-to | deep-dive |
| observability | signals, ownership, correlation, alert intent, blind spots | provider marketing | Reference | deep-dive |
| decision-index / adr | indexed decisions; for each ADR context, decision, alternatives, consequences, status | rewritten history | Explanation | deep-dive |
| flow | trigger, actors, ordered steps, branches, rules, failures, outcome | hand-inferred flow inventory | Explanation | deep-dive |
| runbook | symptom, safety, diagnosis, remediation, verification, escalation | architectural tutorial | How-to | deep-dive |
| repo-inventory | discovered repositories, role, owner token, documentation state, evidence | hand-typed collection omissions | Reference | reference |
| system-context | repository/system boundaries, shared services, cross-repo flows | repo-local internals | Explanation | deep-dive |
| diligence-index | evidence map, gaps, confidence, follow-up | unsupported verdicts | Reference | reference |
| changelog | released versions, dates, user-visible changes, compatibility notes | unreleased aspiration | Reference | reference |
| conventions | evidenced style, structure, error, testing, and review conventions | generic language advice | Reference | deep-dive |
| release-guide | prerequisites, versioning, build, verification, publication, rollback | changelog content | How-to | deep-dive |
| ownership | owned areas, responsibility boundaries, escalation tokens | invented people or teams | Reference | reference |
| glossary | repository terms, precise definitions, owning document links | duplicate flow or architecture prose | Reference | reference |
| rendering / state-management | lifecycle, boundaries, transitions, failure and recovery behavior | component catalog | Explanation | deep-dive |
| environments | environment differences, promotion boundaries, configuration ownership | deployment procedure | Explanation | deep-dive |
| disaster-recovery | failure scenarios, recovery order, verification, data-loss boundary | ordinary deploy steps | How-to | deep-dive |
| compatibility | supported versions/platforms, tested matrix, deprecation behavior | migration procedure | Reference | reference |
| migration | source/target versions, breaking changes, ordered changes, verification, rollback | full compatibility matrix | How-to | deep-dive |
| error-catalog | stable code/name, trigger, client behavior, retryability, observability | implementation stack traces | Reference | reference |
| process-flows | actor, trigger, business-language steps, decision points, exceptions, outcome, owning flow links | raw call chains or repeated business-rule definitions | Explanation | deep-dive |
| business-rules | stable rule id, plain-language statement, trigger, outcome, exceptions, enforcement evidence | rules inferred only from names | Reference | deep-dive |
| requirements-traceability | requirement evidence, owning rule/flow, implementation, test, status | invented ticket identifiers | Reference | deep-dive |
| feature-catalog | user outcome, audience, availability, owning flow | implementation inventory | Reference | deep-dive |
| success-metrics | outcome, measure, instrumentation state, interpretation, external target token | invented targets | Reference | deep-dive |
| release-notes | released user impact, version/date, compatibility impact, feature links | internal refactor and dependency noise | Reference | reference |
| backlog-traceability | evidenced ticket id, feature, flow/change, release/status link | guessed ticket mappings or empty seed tables | Reference | reference |
| portfolio security/operations | cross-repo controls, gaps, shared dependencies, operational coupling | member-level repetition | Explanation | deep-dive |

## Overlay types

- API and library references derive their public surface from specs, schemas, or
  exported interfaces; do not hand-maintain a parallel API.
- Data contracts name producers, consumers, schema, validation, lineage,
  compatibility, and recovery.
- Business Analyst documents own a business-language process view, rules, and
  requirements traceability. The process view links each item to its canonical
  dynamic flow document; it does not duplicate technical call-chain prose.
- Product Owner documents own feature value/status, evidenced measures, and
  user-facing release notes. Backlog traceability is dynamic and exists only
  with ticket evidence.
- Agent views are compact linking views. Architecture and patterns require the
  code graph; only flow and flow-derived glossary views require the flow graph;
  conventions require a conventions source.

The optional instruction file named by the catalog adds writing craft only. It
must not redefine this contract.
