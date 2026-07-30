# Document catalog contracts

This directory owns content contracts: must-present material, keep-out
boundaries, primary mode, and target depth. Selection, paths, evidence
capabilities, write order, templates, and audit profiles are machine-readable
via `query_catalog` against `.metadata/catalog/`.

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

## Index

- `root-readme` — purpose, audience, verified quick start, links to setup/architecture/limitations → [root-readme.md](root-readme.md)
- `docs-index` — selected children and one-line purpose → [docs-index.md](docs-index.md)
- `folder-index` — selected children and one-line purpose → [folder-index.md](folder-index.md)
- `ba-index` — selected children and one-line purpose → [ba-index.md](ba-index.md)
- `po-index` — selected children and one-line purpose → [po-index.md](po-index.md)
- `portfolio-index` — selected children and one-line purpose → [portfolio-index.md](portfolio-index.md)
- `portfolio-decisions-index` — selected children and one-line purpose → [portfolio-decisions-index.md](portfolio-decisions-index.md)
- `product-overview` — users, problems, capabilities, explicit non-goals → [product-overview.md](product-overview.md)
- `tech-stack` — languages/runtimes/frameworks/datastores/build tooling (shape-conditional for IaC) → [tech-stack.md](tech-stack.md)
- `system-overview` — major capabilities, owning flows, primary end-to-end path, boundary systems → [system-overview.md](system-overview.md)
- `epic` — cross-repo initiative outcome, member repos, owning flows, sequence, open gaps → [epic.md](epic.md)
- `architecture-high-level` — context, deployable blocks, boundaries, communication, invariants → [architecture-high-level.md](architecture-high-level.md)
- `architecture-low-level` — subsystem responsibilities, data/control paths, failure boundaries → [architecture-low-level.md](architecture-low-level.md)
- `access` — principals, scopes, grant path, review cadence for who/what can change infrastructure → [access.md](access.md)
- `network` — topology zones, boundary crossings, traffic purpose, enforcement, concentration-risk → [network.md](network.md)
- `versioning` — version scheme, compatibility policy, deprecation window, migration path → [versioning.md](versioning.md)
- `dataset` — dataset identity, producers/consumers, schema ownership, freshness/retention → [dataset.md](dataset.md)
- `setup-guide` — prerequisites, install, configuration, run, verification, recovery → [setup-guide.md](setup-guide.md)
- `testing-guide` — test layers, commands, fixtures, isolation, failure diagnosis → [testing-guide.md](testing-guide.md)
- `configuration` — every read setting, default, scope, sensitivity, validation → [configuration.md](configuration.md)
- `limitations-register` — known bounds, trigger, impact, workaround, source evidence → [limitations-register.md](limitations-register.md)
- `dependencies-inventory` — direct dependencies/integrations, purpose, criticality, failure behavior → [dependencies-inventory.md](dependencies-inventory.md)
- `constraints` — hard bounds with source and design implication; deliberate non-goals → [constraints.md](constraints.md)
- `tech-debt-register` — shortcut, consequence, evidence, remediation direction → [tech-debt-register.md](tech-debt-register.md)
- `security-policy` — supported scope, reporting path, response expectations, safe harbor → [security-policy.md](security-policy.md)
- `threat-model` — assets, trust boundaries, threats, controls, accepted residual risk → [threat-model.md](threat-model.md)
- `data-handling` — data classes, lifecycle, access, retention, deletion → [data-handling.md](data-handling.md)
- `deployment` — environments, artifact path, rollout, rollback, verification → [deployment.md](deployment.md)
- `observability` — signals, ownership, correlation, alert intent, blind spots → [observability.md](observability.md)
- `decision-index` — indexed decisions; for each ADR context, decision, alternatives, consequences, status → [decision-index.md](decision-index.md)
- `adr` — indexed decisions; for each ADR context, decision, alternatives, consequences, status → [adr.md](adr.md)
- `flow-index` — every evidence-backed candidate, normalized entry reference, area, confidence, reach, p… → [flow-index.md](flow-index.md)
- `flow` — trigger, actors, ordered steps, branches, rules, failures, outcome → [flow.md](flow.md)
- `concept` — one durable concept, responsibility, relationships, invariants, failure boundaries → [concept.md](concept.md)
- `runbook` — symptom, safety, diagnosis, remediation, verification, escalation → [runbook.md](runbook.md)
- `repo-inventory` — discovered repositories, role, owner token, documentation state, evidence → [repo-inventory.md](repo-inventory.md)
- `system-context` — repository/system boundaries, shared services, cross-repo flows → [system-context.md](system-context.md)
- `diligence-index` — evidence map, gaps, confidence, follow-up → [diligence-index.md](diligence-index.md)
- `changelog` — released versions, dates, user-visible changes, compatibility notes → [changelog.md](changelog.md)
- `conventions` — evidenced style, structure, error, testing, and review conventions → [conventions.md](conventions.md)
- `release-guide` — prerequisites, versioning, build, verification, publication, rollback → [release-guide.md](release-guide.md)
- `ownership` — owned areas, responsibility boundaries, escalation tokens → [ownership.md](ownership.md)
- `glossary` — repository terms, precise definitions, owning document links → [glossary.md](glossary.md)
- `rendering` — lifecycle, boundaries, transitions, failure and recovery behavior → [rendering.md](rendering.md)
- `state-management` — lifecycle, boundaries, transitions, failure and recovery behavior → [state-management.md](state-management.md)
- `environments` — environment differences, promotion boundaries, configuration ownership → [environments.md](environments.md)
- `disaster-recovery` — failure scenarios, recovery order, verification, data-loss boundary → [disaster-recovery.md](disaster-recovery.md)
- `compatibility` — supported versions/platforms, tested matrix, deprecation behavior → [compatibility.md](compatibility.md)
- `quickstart` — shortest verified path to first useful result, prerequisites, expected output, next links → [quickstart.md](quickstart.md)
- `api-reference` — public surface, inputs/outputs, auth contract, limits, errors, compatibility source → [api-reference.md](api-reference.md)
- `authentication` — public surface, inputs/outputs, auth contract, limits, errors, compatibility source → [authentication.md](authentication.md)
- `rate-limits` — public surface, inputs/outputs, auth contract, limits, errors, compatibility source → [rate-limits.md](rate-limits.md)
- `data-flow` — producers, transformations, contracts, checks, failure/recovery, schema ownership → [data-flow.md](data-flow.md)
- `data-quality` — producers, transformations, contracts, checks, failure/recovery, schema ownership → [data-quality.md](data-quality.md)
- `data-types` — producers, transformations, contracts, checks, failure/recovery, schema ownership → [data-types.md](data-types.md)
- `content-model` — content types, lifecycle, validation, ownership, publishing boundary → [content-model.md](content-model.md)
- `ui-components` — component responsibilities, composition, tokens/themes, browser matrix, degradation → [ui-components.md](ui-components.md)
- `styling` — component responsibilities, composition, tokens/themes, browser matrix, degradation → [styling.md](styling.md)
- `browser-support` — component responsibilities, composition, tokens/themes, browser matrix, degradation → [browser-support.md](browser-support.md)
- `application-lifecycle` — launch/activation/background/termination states, ownership, restoration, failure bounda… → [application-lifecycle.md](application-lifecycle.md)
- `ui-navigation-state` — surfaces, navigation, state ownership, transitions, restoration, error presentation → [ui-navigation-state.md](ui-navigation-state.md)
- `platform-integration` — OS services, adapters, permissions boundary, callbacks, failure and fallback → [platform-integration.md](platform-integration.md)
- `platform-permissions` — requested capability, trigger, user value, denial behavior, settings/recovery, manifest… → [platform-permissions.md](platform-permissions.md)
- `platform-compatibility` — OS/device/architecture matrix, minimums, tested evidence, degradation, deprecation → [platform-compatibility.md](platform-compatibility.md)
- `application-distribution` — artifact, build, signing, packaging, channels, verification, update/rollback → [application-distribution.md](application-distribution.md)
- `offline-installation` — installability, cache/update lifecycle, offline boundaries, invalidation, recovery → [offline-installation.md](offline-installation.md)
- `triggers-and-jobs` — trigger, payload, scheduling, concurrency, ownership, downstream effects → [triggers-and-jobs.md](triggers-and-jobs.md)
- `job-reliability` — retry, idempotency, timeout, backpressure, dead-letter, replay, observability → [job-reliability.md](job-reliability.md)
- `command-reference` — commands/subcommands, arguments, configuration, examples, side effects → [command-reference.md](command-reference.md)
- `output-exit-contract` — stdout/stderr ownership, formats, exit codes, stability, scripting behavior → [output-exit-contract.md](output-exit-contract.md)
- `host-integration` — host contract, activation, contribution points, permissions, compatibility, sandbox, fa… → [host-integration.md](host-integration.md)
- `extension-points` — host contract, activation, contribution points, permissions, compatibility, sandbox, fa… → [extension-points.md](extension-points.md)
- `model-lifecycle` — datasets, training/evaluation, artifact lineage, inference, limitations, drift, ownership → [model-lifecycle.md](model-lifecycle.md)
- `model-card` — datasets, training/evaluation, artifact lineage, inference, limitations, drift, ownership → [model-card.md](model-card.md)
- `persistence` — entities, storage mapping, migrations, transactions, consistency, failure recovery → [persistence.md](persistence.md)
- `ai-integration` — model/provider boundary, prompts/inputs, outputs, evaluation, safety, privacy, failure → [ai-integration.md](ai-integration.md)
- `gameplay-systems` — system boundaries, scenes/assets, loading, save state, platform builds → [gameplay-systems.md](gameplay-systems.md)
- `assets-and-scenes` — system boundaries, scenes/assets, loading, save state, platform builds → [assets-and-scenes.md](assets-and-scenes.md)
- `performance-budgets` — evidenced CPU/GPU/memory/storage/timing limits, measurement, degradation → [performance-budgets.md](performance-budgets.md)
- `hardware-map` — boards, peripherals, protocols, boot/update states, memory/power, failure → [hardware-map.md](hardware-map.md)
- `firmware-lifecycle` — boards, peripherals, protocols, boot/update states, memory/power, failure → [firmware-lifecycle.md](firmware-lifecycle.md)
- `flashing-recovery` — prerequisites, artifact, connection, flashing, verification, rollback/recovery, safety → [flashing-recovery.md](flashing-recovery.md)
- `contract-system` — contracts, storage, authorities, networks, upgrade boundary, economic/security invariants → [contract-system.md](contract-system.md)
- `economic-invariants` — contracts, storage, authorities, networks, upgrade boundary, economic/security invariants → [economic-invariants.md](economic-invariants.md)
- `network-deployment` — network configuration, keys/roles, deployment order, verification, upgrade/rollback → [network-deployment.md](network-deployment.md)
- `infrastructure-apply` — plan/apply safety, external state, locking, ownership, resource inventory, drift, recovery → [infrastructure-apply.md](infrastructure-apply.md)
- `infrastructure-state` — plan/apply safety, external state, locking, ownership, resource inventory, drift, recovery → [infrastructure-state.md](infrastructure-state.md)
- `resources` — plan/apply safety, external state, locking, ownership, resource inventory, drift, recovery → [resources.md](resources.md)
- `publishing` — artifacts, version source, build/sign, registry/channel, verification, rollback/depreca… → [publishing.md](publishing.md)
- `accessibility` — supported behavior, resources/semantics, fallback, verification, known limits → [accessibility.md](accessibility.md)
- `localization` — supported behavior, resources/semantics, fallback, verification, known limits → [localization.md](localization.md)
- `migration` — source/target versions, breaking changes, ordered changes, verification, rollback → [migration.md](migration.md)
- `error-catalog` — stable code/name, trigger, client behavior, retryability, observability → [error-catalog.md](error-catalog.md)
- `process-flows` — actor, trigger, business-language steps, decision points, exceptions, outcome, owning f… → [process-flows.md](process-flows.md)
- `business-rules` — stable rule id, plain-language statement, trigger, outcome, exceptions, enforcement evi… → [business-rules.md](business-rules.md)
- `requirements-traceability` — requirement evidence, owning rule/flow, implementation, test, status → [requirements-traceability.md](requirements-traceability.md)
- `feature-catalog` — user outcome, audience, availability, owning flow → [feature-catalog.md](feature-catalog.md)
- `success-metrics` — outcome, measure, instrumentation state, interpretation, external target token → [success-metrics.md](success-metrics.md)
- `release-notes` — released user impact, version/date, compatibility impact, feature links → [release-notes.md](release-notes.md)
- `backlog-traceability` — evidenced ticket id, feature, flow/change, release/status link → [backlog-traceability.md](backlog-traceability.md)
- `contributing-router` — verified contribution path, required checks, conventions and ownership links → [contributing-router.md](contributing-router.md)
- `agents-kernel` — compact entry points, verified commands, precedence, safe links to owning agent views → [agents-kernel.md](agents-kernel.md)
- `fixed-shim` — compact entry points, verified commands, precedence, safe links to owning agent views → [fixed-shim.md](fixed-shim.md)
- `machine-config` — compact entry points, verified commands, precedence, safe links to owning agent views → [machine-config.md](machine-config.md)
- `agents-architecture` — token-budgeted retrieval view, durable paths, constraints, verified commands, owning hu… → [agents-architecture.md](agents-architecture.md)
- `agents-patterns` — token-budgeted retrieval view, durable paths, constraints, verified commands, owning hu… → [agents-patterns.md](agents-patterns.md)
- `agents-testing` — token-budgeted retrieval view, durable paths, constraints, verified commands, owning hu… → [agents-testing.md](agents-testing.md)
- `agents-tech-debt` — token-budgeted retrieval view, durable paths, constraints, verified commands, owning hu… → [agents-tech-debt.md](agents-tech-debt.md)
- `agents-conventions` — token-budgeted retrieval view, durable paths, constraints, verified commands, owning hu… → [agents-conventions.md](agents-conventions.md)
- `agents-flow` — compact flow/term lookup grounded in declared flow evidence and linked owners → [agents-flow.md](agents-flow.md)
- `agents-glossary` — compact flow/term lookup grounded in declared flow evidence and linked owners → [agents-glossary.md](agents-glossary.md)
- `security-posture` — cross-repo controls, gaps, shared dependencies, operational coupling → [security-posture.md](security-posture.md)
- `portfolio-operations` — cross-repo controls, gaps, shared dependencies, operational coupling → [portfolio-operations.md](portfolio-operations.md)
- `portfolio-decision` — cross-repository decision evidence or shared terminology with member links → [portfolio-decision.md](portfolio-decision.md)
- `portfolio-glossary` — cross-repository decision evidence or shared terminology with member links → [portfolio-glossary.md](portfolio-glossary.md)

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
