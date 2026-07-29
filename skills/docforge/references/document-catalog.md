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
| docs-index / folder-index / ba-index / po-index / portfolio-index / portfolio-decisions-index | selected children and one-line purpose | unselected or future links | Orientation | orientation |
| product-overview | users, problems, capabilities, explicit non-goals | invented roadmap or implementation detail | Explanation | orientation |
| architecture-high-level | context, deployable blocks, boundaries, communication, invariants | decision rationale and code listings | Explanation | deep-dive |
| architecture-low-level | subsystem responsibilities, data/control paths, failure boundaries | duplicated high-level map | Explanation | deep-dive |
| setup-guide | prerequisites, install, configuration, run, verification, recovery | unverified commands | How-to | deep-dive |
| testing-guide | test layers, commands, fixtures, isolation, failure diagnosis | generic testing advice | How-to | deep-dive |
| configuration | every read setting, default, scope, sensitivity, validation | secrets or aspirational settings | Reference | reference |
| limitations-register | known bounds, trigger, impact, workaround, source evidence | hidden issues or roadmap promises | Reference | deep-dive |
| dependencies-inventory | direct dependencies/integrations, purpose, criticality, failure behavior | generated lockfile dump | Reference | deep-dive |
| constraints | hard bounds with source and design implication; deliberate non-goals | temporary shortcuts, tech-debt items, user-visible limitations | Explanation | deep-dive |
| tech-debt-register | shortcut, consequence, evidence, remediation direction | hard constraints | Reference | deep-dive |
| security-policy | supported scope, reporting path, response expectations, safe harbor | threat-model detail | Reference | router |
| threat-model | assets, trust boundaries, threats, controls, accepted residual risk | disclosure workflow; credentials; unremediated vulnerability detail | Explanation | deep-dive |
| data-handling | data classes, lifecycle, access, retention, deletion | invented compliance claims; credentials; internal hostnames; individual names as security contacts | Reference | deep-dive |
| deployment | environments, artifact path, rollout, rollback, verification | incident procedures | How-to | deep-dive |
| observability | signals, ownership, correlation, alert intent, blind spots | provider marketing | Reference | deep-dive |
| decision-index / adr | indexed decisions; for each ADR context, decision, alternatives, consequences, status | rewritten history | Explanation | deep-dive |
| flow-index | every evidence-backed candidate, normalized entry reference, area, confidence, reach, priority, and main/deferred/placeholder/documented/skipped status | one row per heuristic process or invented execution order | Reference | orientation |
| flow | trigger, actors, ordered steps, branches, rules, failures, outcome | hand-inferred flow inventory | Explanation | deep-dive |
| concept | one durable concept, responsibility, relationships, invariants, failure boundaries | symbol-by-symbol implementation tour | Explanation | deep-dive |
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
| quickstart | shortest verified path to first useful result, prerequisites, expected output, next links | complete setup duplication | How-to | deep-dive |
| api-reference / authentication / rate-limits | public surface, inputs/outputs, auth contract, limits, errors, compatibility source | hand-copied generated schema or secrets | Reference | reference |
| data-flow / data-quality / data-types | producers, transformations, contracts, checks, failure/recovery, schema ownership | unevidenced lineage or sample-only guarantees | Explanation | deep-dive |
| content-model | content types, lifecycle, validation, ownership, publishing boundary | editorial strategy unsupported by repository evidence | Explanation | deep-dive |
| ui-components / styling / browser-support | component responsibilities, composition, tokens/themes, browser matrix, degradation | screenshot catalog or invented support claims | Reference | reference |
| application-lifecycle | launch/activation/background/termination states, ownership, restoration, failure boundaries | UI component inventory | Explanation | deep-dive |
| ui-navigation-state | surfaces, navigation, state ownership, transitions, restoration, error presentation | visual design token catalog | Explanation | deep-dive |
| platform-integration | OS services, adapters, permissions boundary, callbacks, failure and fallback | generic platform API tutorial | Explanation | deep-dive |
| platform-permissions | requested capability, trigger, user value, denial behavior, settings/recovery, manifest evidence | invented entitlement or policy claims | Reference | deep-dive |
| platform-compatibility | OS/device/architecture matrix, minimums, tested evidence, degradation, deprecation | release procedure | Reference | reference |
| application-distribution | artifact, build, signing, packaging, channels, verification, update/rollback | secret material or unsupported store claims | How-to | deep-dive |
| offline-installation | installability, cache/update lifecycle, offline boundaries, invalidation, recovery | generic service-worker tutorial | Explanation | deep-dive |
| triggers-and-jobs | trigger, payload, scheduling, concurrency, ownership, downstream effects | runbook remediation | Explanation | deep-dive |
| job-reliability | retry, idempotency, timeout, backpressure, dead-letter, replay, observability | business process duplication | Reference | deep-dive |
| command-reference | commands/subcommands, arguments, configuration, examples, side effects | implementation call graph | Reference | reference |
| output-exit-contract | stdout/stderr ownership, formats, exit codes, stability, scripting behavior | prose-only examples without verified output | Reference | reference |
| host-integration / extension-points | host contract, activation, contribution points, permissions, compatibility, sandbox, failure | host product tutorial | Explanation | deep-dive |
| model-lifecycle / model-card | datasets, training/evaluation, artifact lineage, inference, limitations, drift, ownership | unsupported quality or safety claims | Explanation | deep-dive |
| persistence | entities, storage mapping, migrations, transactions, consistency, failure recovery | ORM tutorial or invented schema | Explanation | deep-dive |
| ai-integration | model/provider boundary, prompts/inputs, outputs, evaluation, safety, privacy, failure | unsupported model quality claims or training-system docs (see model-lifecycle) | Explanation | deep-dive |
| gameplay-systems / assets-and-scenes | system boundaries, scenes/assets, loading, save state, platform builds | design-document aspiration | Explanation | deep-dive |
| performance-budgets | evidenced CPU/GPU/memory/storage/timing limits, measurement, degradation | invented targets | Reference | reference |
| hardware-map / firmware-lifecycle | boards, peripherals, protocols, boot/update states, memory/power, failure | generic component datasheets | Explanation | deep-dive |
| flashing-recovery | prerequisites, artifact, connection, flashing, verification, rollback/recovery, safety | unverified destructive commands | How-to | deep-dive |
| contract-system / economic-invariants | contracts, storage, authorities, networks, upgrade boundary, economic/security invariants | unsupported audit verdict | Explanation | deep-dive |
| network-deployment | network configuration, keys/roles, deployment order, verification, upgrade/rollback | private keys or fabricated addresses | How-to | deep-dive |
| infrastructure-apply / infrastructure-state / resources | plan/apply safety, external state, locking, ownership, resource inventory, drift, recovery | credentials or unverified destructive commands | Reference | deep-dive |
| publishing | artifacts, version source, build/sign, registry/channel, verification, rollback/deprecation | secret values or changelog duplication | How-to | deep-dive |
| accessibility / localization | supported behavior, resources/semantics, fallback, verification, known limits | compliance claims without evidence | Reference | deep-dive |
| migration | source/target versions, breaking changes, ordered changes, verification, rollback | full compatibility matrix | How-to | deep-dive |
| error-catalog | stable code/name, trigger, client behavior, retryability, observability | implementation stack traces | Reference | reference |
| process-flows | actor, trigger, business-language steps, decision points, exceptions, outcome, owning flow links | raw call chains or repeated business-rule definitions | Explanation | deep-dive |
| business-rules | stable rule id, plain-language statement, trigger, outcome, exceptions, enforcement evidence | rules inferred only from names | Reference | deep-dive |
| requirements-traceability | requirement evidence, owning rule/flow, implementation, test, status | invented ticket identifiers | Reference | deep-dive |
| feature-catalog | user outcome, audience, availability, owning flow | implementation inventory | Reference | deep-dive |
| success-metrics | outcome, measure, instrumentation state, interpretation, external target token | invented targets | Reference | deep-dive |
| release-notes | released user impact, version/date, compatibility impact, feature links | internal refactor and dependency noise | Reference | reference |
| backlog-traceability | evidenced ticket id, feature, flow/change, release/status link | guessed ticket mappings or empty seed tables | Reference | reference |
| contributing-router | verified contribution path, required checks, conventions and ownership links | duplicated setup/testing guides | Orientation | router |
| agents-kernel / fixed-shim / machine-config | compact entry points, verified commands, precedence, safe links to owning agent views | broad narrative, invented settings, or overwritten user configuration | Orientation | router |
| agents-architecture / agents-patterns / agents-testing / agents-tech-debt / agents-conventions | token-budgeted retrieval view, durable paths, constraints, verified commands, owning human-doc links | duplicated human documentation or volatile symbol dumps | Reference | deep-dive |
| agents-flow / agents-glossary | compact flow/term lookup grounded in declared flow evidence and linked owners | inferred flows or duplicated business prose | Reference | reference |
| security-posture / portfolio-operations | cross-repo controls, gaps, shared dependencies, operational coupling | member-level repetition | Explanation | deep-dive |
| portfolio-decision / portfolio-glossary | cross-repository decision evidence or shared terminology with member links | repository-local ADR duplication | Reference | deep-dive |

## Risk-register routing

Route each bound by who can change it and whether it is user-visible: fixable by
us later → `tech-debt-register`; imposed from outside and immovable →
`constraints`; deliberate or accepted and user-visible → `limitations-register`.
Never cross-file them. For `threat-model`, keep the analysis proportionate; the
accepted-risk section is the reviewer's signal that analysis was performed.
When more rigor is warranted, use a trust-boundary data-flow with STRIDE per
element and one response per threat (mitigate / eliminate / transfer / accept)
tied to a testable control — link `data-handling` classifications; do not
restate the inventory.

## Typed profile behavior

- Shapes own document packs. API and library references derive their public surface from specs, schemas, or
  exported interfaces; do not hand-maintain a parallel API.
- Platforms own runtime compatibility, permissions, lifecycle, packaging,
  signing, and distribution details inside the shared client documents.
- Framework profiles change detection, graph queries, terminology, and verified
  commands only. They do not create `flutter-*`, `electron-*`, or equivalent
  duplicate document families.
- Concerns add a document only when the catalog explicitly owns one; otherwise
  they add a section to the existing topic owner.
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
